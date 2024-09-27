import os
import pandas as pd
import main

def view_csv():    
    # CSV 파일 경로 설정
    csv_path = 'detections.csv'
    
    # CSV 파일이 존재하는지 확인
    if not os.path.isfile(csv_path):
        return f"CSV 파일이 {csv_path}에 존재하지 않습니다."
    
    try:
        # pandas로 CSV 파일 읽기
        df = pd.read_csv(csv_path, header=None, names=['name', 'confidence'])
        
        # CSV 파일의 첫 번째 열: 'name' (인식된 객체)
        # 두 번째 열: 'confidence' (인식률)
        if 'name' not in df.columns or 'confidence' not in df.columns:
            return "CSV 파일 형식이 올바르지 않습니다. 'name'과 'confidence' 열이 필요합니다."
        
        # 'kids' 또는 'adult'가 인식된 경우 창문을 여는 신호 전달
        if df['name'].str.contains('kids|adult').any():
            main.door_control('open')
        
        # HTML 테이블로 변환하여 웹페이지에 표시
        data = df.to_html(classes='table table-striped', index=False)
        return data
    except Exception as e:
        # 에러가 발생한 경우 에러 메시지 반환
        return f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"
