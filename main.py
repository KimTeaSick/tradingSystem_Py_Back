from api.Kiwoom import *
import sys

app = QApplication(sys.argv)
kiwoom = Kiwoom()

kospi_code_list = kiwoom.get_code_list_market("0")

df = kiwoom.get_price_data("005930")
print(df)
# for code in kospi_code_list:
#     code_name = kiwoom.get_master_code_name(code)
#     print(code, code_name)
app.exec_()