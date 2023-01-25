from flask import Flask
from api.Kiwoom import *
import sys

app = Flask(__name__)

kiwoomApp = QApplication(sys.argv)
kiwoom = Kiwoom()
# kiwoom.get_deposit()
# order_result = kiwoom.send_order('send_buy_order', '1001', 1, '007700', 1, 35000, '00')
# kospi_code_list = kiwoom.get_code_list_market("0")
# df = kiwoom.get_price_data("005930")
# print(df)
# for code in kospi_code_list:
#     code_name = kiwoom.get_master_code_name(code)
#     print(code, code_name)
#
# print("order_result ::: ", order_result)
# kiwoomApp.exec_()
@app.route('/')
def hello_world():
    return kiwoom.account_number


if __name__ == '__main__':
    app.run()



# print(order_result)
