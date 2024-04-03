import time
import dbconn
import upbitconn
import pyupbit
import math

bidcnt = 1
def loadmyset(uno):
    mysett = dbconn.getsetups(uno)
    return mysett


def getkeys(uno):
    mykey = dbconn.getupbitkey(uno)
    return mykey


def getorders(key1, key2, coinn):
    upbit = pyupbit.Upbit(key1, key2)
    orders = upbit.get_order(coinn)
    return orders


def buymarketpr(key1, key2, coinn, camount):
    upbit = pyupbit.Upbit(key1,key2)
    orders = upbit.buy_market_order(coinn, camount)
    return orders


def buylimitpr(key1, key2, coinn, setpr, setvol):
    upbit = pyupbit.Upbit(key1, key2)
    orders = upbit.buy_limit_order(coinn,setpr,setvol)
    return orders


def sellmarketpr(key1, key2, coinn, setvol):
    upbit = pyupbit.Upbit(key1, key2)
    orders = upbit.sell_market_order(coinn,setvol)
    return orders

def selllimitpr(key1, key2, coinn, setpr, setvol):
    upbit = pyupbit.Upbit(key1,key2)
    orders = upbit.sell_limit_order(coinn,setpr,setvol)
    return orders

def checktraded(key1, key2, coinn):
    upbit = pyupbit.Upbit(key1,key2)
    checktrad = upbit.get_balances()
    for wallet in checktrad:
        if "KRW-" + wallet['currency'] == coinn:
            if float(wallet['balance']) != 0.0:
                print("잔고 남아 재거래")
            else:
                print('매도 거래 대기중')
            return wallet
        else:
            pass
    if checktrad is None:
        pass


def calprice(bidprice):
    if bidprice >= 2000000:
        bidprice = round(bidprice, -3)
    elif bidprice >= 1000000 and bidprice < 20000000:
        bidprice = round(bidprice, -3) + 500
    elif bidprice >= 500000 and bidprice < 1000000:
        bidprice = round(bidprice, -2)
    elif bidprice >= 100000 and bidprice < 500000:
        bidprice = round(bidprice, -2) + 50
    elif bidprice >= 10000 and bidprice < 100000:
        bidprice = round(bidprice, -1)
    elif bidprice >= 1000 and bidprice < 10000:
        bidprice = round(bidprice)
    elif bidprice >= 100 and bidprice < 1000:
        bidprice = round(bidprice, 1)
    elif bidprice >= 10 and bidprice < 100:
        bidprice = round(bidprice, 2)
    elif bidprice >= 1 and bidprice < 10:
        bidprice = round(bidprice, 3)
    else:
        bidprice = round(bidprice, 4)
    return bidprice


def cancelaskorder(key1,key2,coinn):
    upbit = pyupbit.Upbit(key1, key2)
    orders = upbit.get_order(coinn)
    for order in orders:
        print(order)
        if order['side'] == 'ask':
            upbit.cancel_order(order['uuid'])
            print("Canceled")

def canclebidorder(key1, key2, coinn): #코인 청산
    upbit = pyupbit.Upbit(key1,key2)
    orders = upbit.get_order(coinn)
    if len(orders)>0:
        for order in orders:
            upbit.cancel_order(order["uuid"])
    else:
        pass

def checkbidorder(key1,key2,coinn):
    upbit = pyupbit.Upbit(key1, key2)
    orders = upbit.get_order(coinn)
    for order in orders:
        if order['side'] == 'bid':
            return True
        else:
            return False


def runorders():
    setons = dbconn.getseton()
    if setons is not None:
        for seton in setons:
            keys = getkeys(seton)
            myset = loadmyset(seton)
            items = getorders(keys[0], keys[1], myset[6])
            if myset[7] == 'Y': #거래 개시인 것만
                iniAsset = myset[2]
                interVal = myset[3]
                intergap = myset[4]
                intRate = myset[5]
                coinn = myset[6]
                preprice = pyupbit.get_current_price(coinn)
                print('현재가', preprice)
                traded = checktraded(keys[0], keys[1], coinn)
                print("지갑확인 :",traded)
                if traded is not None:
                    if float(traded['balance']) != 0.0:
                        print('보유수량 변화')
                        if float(traded['locked']) == 0.0:
                            print('최초 매도 수행')
                            if globals()['lcnt_{}'.format(seton[0])] == 1:
                                setprice = preprice * (1.007+(intRate / 100.0))
                                globals()['lcnt_{}'.format(seton[0])] == 0
                            else:
                                setprice = preprice * (1.0 + (intRate / 100.0))
                            setprice = calprice(setprice)
                            setvolume = traded['balance']
                            selllimitpr(keys[0], keys[1], coinn, setprice, setvolume)
                        elif float(traded['locked']) != 0.0:
                            cancelaskorder(keys[0], keys[1], coinn)
                            globals()['bcnt_{}'.format(seton[0])] = 1
                            globals()['lcnt_{}'.format(seton[0])] = 1
                            print('매도주문 재송신')
                    else:
                        print('거래중')
                else:
                    canclebidorder(keys[0], keys[1], coinn)
                    globals()['bcnt_{}'.format(seton[0])] = 1
                bidasset = iniAsset
                if globals()['bcnt_{}'.format(seton[0])] <= 1 :
                    buymarketpr(keys[0], keys[1], coinn, iniAsset) # 첫번째 설정 구매
                    #기존 주문 취소
                    for i in range(1,interVal+1):
                        bidprice = ((preprice * 100) - (preprice * intergap*i)) / 100
                        bidprice = calprice(bidprice)
                        bidasset = bidasset * 2
                        bidvol = bidasset / bidprice
                        print('interval ',i,'예약 거래 적용')
                        print('매수가격',bidprice)
                        print('매수금액',bidasset)
                        print('매수수량',bidvol)
                        if globals()['bcnt_{}'.format(seton[0])] <=1 :
                            buylimitpr(keys[0],keys[1],coinn, bidprice,bidvol)
                            print("매수 실행")
                        else:
                            print("매수 PASS")
                            pass
                    # 설정된 추가 매수예약 진행
                else:
                    print('매도 거래 대기')
                print('거래 개시')
                globals()['bcnt_{}'.format(seton[0])] = globals()['bcnt_{}'.format(seton[0])] + 1
                print("거래점검 횟수", globals()['bcnt_{}'.format(seton[0])])
                print('-----------------------')
            else:#거래 대기 상태
                print("거래 대기", seton[0])
                myset = loadmyset(seton)
                coinn = myset[6]
                canclebidorder(keys[0], keys[1], coinn)
                print('-----------------------')
                globals()['bcnt_{}'.format(seton[0])] = 1

    else:
        print("No seton found!!")
    dbconn.clearcache()


cnt = 1

setons = dbconn.getseton()
for seton in setons:
    globals()['bcnt_{}'.format(seton[0])]=1
    globals()['lcnt_{}'.format(seton[0])]=0

while True:
    print("Count : ", cnt)
    runorders()
    cnt = cnt+1
    time.sleep(3)
