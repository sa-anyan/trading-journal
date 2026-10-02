###########################################################################
# TRADING JOURNAL - PAPER TRADING ACTIVITY LOG PARSER
###########################################################################
import hashlib
import re
import pandas as pd

CALL_RE = re.compile(r"Call to place market order to (?P<side>buy|sell)\s+(?P<qty>[\d,]+(?:\.\d+)?)\s+units of symbol (?P<symbol>[A-Z0-9:._-]+)(?:\s+with SL (?P<sl>[\d.]+) and TP (?P<tp>[\d.]+))?", re.I)
EXEC_RE = re.compile(r"Order (?P<order_id>\d+) for symbol (?P<symbol>[A-Z0-9:._-]+) has been executed at price (?P<price>[\d.]+) for (?P<qty>[\d,]+(?:\.\d+)?) units", re.I)
MODIFY_RE = re.compile(r"Modify position for symbol (?P<symbol>[A-Z0-9:._-]+) with SL (?P<sl>[\d.]+) and TP (?P<tp>[\d.]+)", re.I)

def _symbol(s): return str(s or '').upper().strip().split(':')[-1]
def _num(v): return None if v in (None,'') or pd.isna(v) else float(str(v).replace(',','').strip())
def _dir(side): return 'Long' if str(side).lower()=='buy' else 'Short'
def _ret(direction,entry,exit_price):
    move=(exit_price-entry) if direction=='Long' else (entry-exit_price)
    return (move/entry*100.0) if entry else 0.0
def _pnl(direction,entry,exit_price,qty):
    move=(exit_price-entry) if direction=='Long' else (entry-exit_price)
    return move*qty

def parse_paper_activity_log(file_or_path, filename=None):
    df=pd.read_csv(file_or_path)
    missing={'Time','Text'}-set(df.columns)
    if missing: raise ValueError('Not a recognised TradingView Paper Trading Activity Log. Missing: '+', '.join(sorted(missing)))
    d=df.copy(); d['_row_order']=range(len(d)); d['Time']=pd.to_datetime(d['Time'],dayfirst=True,errors='raise')
    d=d.sort_values(['Time','_row_order'],ascending=[True,False],kind='stable').reset_index(drop=True)
    pending=[]; open_pos={}; completed=[]; trade_no=0
    for _,row in d.iterrows():
        ts=row['Time']; text=str(row['Text'])
        m=CALL_RE.search(text)
        if m:
            pending.append({'side':m.group('side').lower(),'qty':_num(m.group('qty')),'symbol':_symbol(m.group('symbol')),'sl':_num(m.group('sl')),'tp':_num(m.group('tp'))}); continue
        m=MODIFY_RE.search(text)
        if m:
            s=_symbol(m.group('symbol'))
            if s in open_pos:
                open_pos[s]['final_stop_price']=_num(m.group('sl')); open_pos[s]['final_take_profit_price']=_num(m.group('tp')); open_pos[s]['modification_count']+=1
            continue
        m=EXEC_RE.search(text)
        if not m: continue
        s=_symbol(m.group('symbol')); qty=_num(m.group('qty')); price=_num(m.group('price')); oid=m.group('order_id')
        idx=next((i for i in range(len(pending)-1,-1,-1) if pending[i]['symbol']==s and abs(pending[i]['qty']-qty)<1e-12),None)
        if idx is None: continue
        intent=pending.pop(idx); side=intent['side']
        if s not in open_pos:
            open_pos[s]={'direction':_dir(side),'entry_side':side,'entry_time':ts,'entry_price':price,'quantity':qty,'entry_order_id':oid,'initial_stop_price':intent['sl'],'initial_take_profit_price':intent['tp'],'final_stop_price':intent['sl'],'final_take_profit_price':intent['tp'],'modification_count':0}; continue
        pos=open_pos[s]; same=(pos['direction']=='Long' and side=='buy') or (pos['direction']=='Short' and side=='sell')
        if same:
            old=pos['quantity']; new=old+qty; pos['entry_price']=(pos['entry_price']*old+price*qty)/new; pos['quantity']=new
            if pos['initial_stop_price'] is None and intent['sl'] is not None: pos['initial_stop_price']=intent['sl']
            if pos['initial_take_profit_price'] is None and intent['tp'] is not None: pos['initial_take_profit_price']=intent['tp']
            if intent['sl'] is not None: pos['final_stop_price']=intent['sl']
            if intent['tp'] is not None: pos['final_take_profit_price']=intent['tp']
            continue
        close_qty=min(qty,pos['quantity']); trade_no+=1
        uid=hashlib.sha256(f"paper|{s}|{pos['entry_time']}|{ts}|{pos['entry_price']}|{price}|{close_qty}|{pos['entry_order_id']}|{oid}".encode()).hexdigest()[:24]
        completed.append({'trade_uid':uid,'trade_number':trade_no,'symbol':s,'direction':pos['direction'],'entry_time':pos['entry_time'],'exit_time':ts,'entry_signal':f"Paper market {pos['entry_side']} order",'exit_signal':f"Paper market {side} close",'entry_price':pos['entry_price'],'exit_price':price,'quantity':close_qty,'position_value':pos['entry_price']*close_qty,'net_pnl':_pnl(pos['direction'],pos['entry_price'],price,close_qty),'return_pct':_ret(pos['direction'],pos['entry_price'],price),'commission':0.0,'favorable_excursion':None,'favorable_excursion_pct':None,'adverse_excursion':None,'adverse_excursion_pct':None,'duration_bars':None,'duration_seconds':int((ts-pos['entry_time']).total_seconds()),'planned_stop_price':pos['initial_stop_price'],'initial_take_profit_price':pos['initial_take_profit_price'],'final_stop_price':pos['final_stop_price'],'final_take_profit_price':pos['final_take_profit_price'],'entry_order_id':pos['entry_order_id'],'exit_order_id':oid,'stop_source':'Paper Trading Activity Log' if pos['initial_stop_price'] is not None else '','pnl_source':'Estimated: price movement × units','modification_count':pos['modification_count']})
        pos['quantity']-=close_qty
        if pos['quantity']<=1e-12: del open_pos[s]
    return pd.DataFrame(completed)
