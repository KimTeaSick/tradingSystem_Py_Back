from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pandas as pd
import time
from util.const import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()

        self.account_number = self.get_account_number()
        self.tr_event_loop = QEventLoop()

        self.order = {}
        self.balance = {}

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._login_slot)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)
        self.OnReceiveChejanData.connect(self._on_chejan_slot)
    def _login_slot(self, err_code):
        if err_code == 0:
            print("connect")
        else:
            print("fail")

        self.login_event_loop.exit()

    def _comm_connect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"):
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)
        account_number = account_list.split(';')[0]
        print('account_number', account_number)
        return account_number

    def get_code_list_market(self, market_type):
        code_list = self.dynamicCall("GetCodeListByMarket(QString", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data(self, code):
        self.dynamicCall("SetInputValue(QString,QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")
        self.tr_event_loop.exec_()
        ohlcv = self.tr_data

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString,QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():
                print("key", key)
                ohlcv[key] += val

            df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])

            return df[::-1]

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        print("[kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":
            ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv
        elif rqname == "opw00001_req":
            deposit = self.dynamicCall("GetCommData(QString,QString,int,QString)", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print(self.tr_data)

        self.tr_event_loop.exit()
        time.sleep(0.5)

    def get_deposit(self):
        self.dynamicCall("SetInputValue(QString,QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString,QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString,QString)", "조회번호", "2")
        self.dynamicCall("CommRqData(QString,QString,int,QString)", "opw00001_req", "opw00001", 0, "0002")
        self.tr_event_loop.exec_()

        return self.tr_data

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification, origin_order_number=""):
        order_result = self.dynamicCall("SendOrder(QString,QString,QString,int,QString,int,int,QString,QString)",
                                        [rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price, order_classification, origin_order_number])
        return order_result

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("[Kiwoom] on recevie msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode, msg))

    def _on_chejan_slot(self, s_gubun, n_item, s_fid_list):
        print("[Kiwoom] on chejan slot is called {} / {} / {}".format(s_gubun, n_item, s_fid_list))

        for fid in s_fid_list.split(';'):
            if fid in FID_CODES:
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]
                data = self.dynamicCall("GetChejanData(int)", fid)

                data = data.strip().lstrip('+').lstrip('-')

                if data.isdigit():
                    data = int (data)

                item_name = FID_CODES[fid]
                print("{} : {}".format(item_name, data))

                if int(s_gubun) == 0:
                    if code not in self.order.keys():
                        self.order[code] = {}

                    self.order[code].update({item_name: data})
                elif int(s_gubun) == 1:
                    if code not in self.balance.keys():
                        self.balance[code] = {}

                    self.balance[code].update({item_name: data})
            if int(s_gubun) == 0:
                print("주문출력(self.order)")
                print(self.order)
            elif int(s_gubun) == 1:
                print("잔고출력(self.balance)")
                print(self.balance)

