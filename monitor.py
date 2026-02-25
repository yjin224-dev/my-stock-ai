import FinanceDataReader as fdr
import pandas as pd

def get_stock_list():
    """
    한국 거래소(KRX) 상장 종목 리스트를 가져옵니다.
    """
    print("종목 리스트를 불러오는 중입니다...")
    df_krx = fdr.StockListing('KRX')
    
    # 상위 5개 종목만 샘플로 출력
    print(df_krx[['Code', 'Name', 'Market']].head())
    return df_krx

if __name__ == "__main__":
    stocks = get_stock_list()
    print(f"총 {len(stocks)}개의 종목을 찾았습니다.")
