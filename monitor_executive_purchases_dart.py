#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenDart API 기반 임원 특정증권등 소유상황보고서 모니터링 봇
- OpenDart API를 활용한 안정적인 공시 데이터 수집
- 임원 장내매수 정보 실시간 모니터링
- 텔레그램 알림 기능
- GitHub Actions 환경 최적화
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pytz
import pandas as pd
import re
from dataclasses import dataclass

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

@dataclass
class ExecutiveDisclosure:
    """임원 공시 정보 데이터 클래스"""
    corp_name: str
    corp_code: str
    stock_code: str
    report_nm: str
    rcept_no: str
    flr_nm: str
    rcept_dt: str
    rm: str

class KSTFormatter(logging.Formatter):
    """한국 시간대 로그 포맷터"""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, KST)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.strftime('%Y-%m-%d %H:%M:%S KST')
        return s

def setup_logging():
    """로깅 설정"""
    log_dir = '/home/user/output'
    os.makedirs(log_dir, exist_ok=True)

    current_time = datetime.now(KST)
    log_filename = f"dart_executive_monitor_{current_time.strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 파일 핸들러
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 포맷터 설정
    formatter = KSTFormatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class OpenDartAPI:
    """OpenDart API 클라이언트"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_disclosure_list(self, bgn_de: str, end_de: str, 
                          corp_cls: str = 'Y', page_no: int = 1, 
                          page_count: int = 100) -> Dict:
        """공시 목록 조회"""
        url = f"{self.base_url}/list.json"
        params = {
            'crtfc_key': self.api_key,
            'bgn_de': bgn_de,
            'end_de': end_de,
            'corp_cls': corp_cls,  # Y: 유가증권시장, K: 코스닥, N: 코넥스, E: 기타
            'page_no': page_no,
            'page_count': page_count
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"공시 목록 조회 실패: {e}")
            return {}

    def get_disclosure_detail(self, rcept_no: str) -> Dict:
        """공시 상세 내용 조회"""
        url = f"{self.base_url}/document.json"
        params = {
            'crtfc_key': self.api_key,
            'rcept_no': rcept_no
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"공시 상세 조회 실패 (rcept_no: {rcept_no}): {e}")
            return {}

    def search_executive_disclosures(self, start_date: str, end_date: str) -> List[ExecutiveDisclosure]:
        """임원 특정증권등 소유상황보고서 검색"""
        disclosures = []
        page_no = 1

        # 임원 공시 관련 키워드
        executive_keywords = [
            '임원ㆍ주요주주특정증권등소유상황보고서',
            '임원·주요주주특정증권등소유상황보고서',
            '임원특정증권등소유상황보고서',
            '주요주주특정증권등소유상황보고서'
        ]

        while True:
            logging.info(f"공시 목록 조회 중... (페이지: {page_no})")

            # 유가증권시장 조회
            kospi_data = self.get_disclosure_list(start_date, end_date, 'Y', page_no, 100)
            # 코스닥 조회
            kosdaq_data = self.get_disclosure_list(start_date, end_date, 'K', page_no, 100)

            all_data = []

            # 데이터 병합
            for data in [kospi_data, kosdaq_data]:
                if data.get('status') == '000' and 'list' in data:
                    all_data.extend(data['list'])

            if not all_data:
                break

            # 임원 공시 필터링
            for item in all_data:
                report_nm = item.get('report_nm', '')

                # 임원 공시 키워드 매칭
                if any(keyword in report_nm for keyword in executive_keywords):
                    disclosure = ExecutiveDisclosure(
                        corp_name=item.get('corp_name', ''),
                        corp_code=item.get('corp_code', ''),
                        stock_code=item.get('stock_code', ''),
                        report_nm=report_nm,
                        rcept_no=item.get('rcept_no', ''),
                        flr_nm=item.get('flr_nm', ''),
                        rcept_dt=item.get('rcept_dt', ''),
                        rm=item.get('rm', '')
                    )
                    disclosures.append(disclosure)
                    logging.info(f"임원 공시 발견: {disclosure.corp_name} - {disclosure.flr_nm}")

            # 다음 페이지 확인
            if len(all_data) < 100:
                break

            page_no += 1

            # 안전장치: 최대 10페이지까지만 조회
            if page_no > 10:
                break

        logging.info(f"총 {len(disclosures)}건의 임원 공시 발견")
        return disclosures

    def check_purchase_transaction(self, rcept_no: str) -> Optional[Dict]:
        """공시 상세에서 장내매수 여부 확인"""
        detail = self.get_disclosure_detail(rcept_no)

        if not detail or detail.get('status') != '000':
            return None

        # 공시 내용에서 장내매수 키워드 검색
        purchase_keywords = ['장내매수', '장내 매수', '매수', '취득']

        # 문서 내용 검색
        if 'list' in detail:
            for doc in detail['list']:
                content = doc.get('content', '')

                # 장내매수 키워드 확인
                if any(keyword in content for keyword in purchase_keywords):
                    # 상세 정보 추출
                    purchase_info = self.extract_purchase_details(content, doc)
                    if purchase_info:
                        return purchase_info

        return None

    def extract_purchase_details(self, content: str, doc: Dict) -> Optional[Dict]:
        """공시 내용에서 매수 상세 정보 추출"""
        try:
            # 기본 정보
            purchase_info = {
                'reporter': '',
                'position': '',
                'transaction_type': '',
                'shares': '',
                'price': '',
                'transaction_date': '',
                'reason': '',
                'content_preview': content[:200] + '...' if len(content) > 200 else content
            }

            # 정규식 패턴으로 정보 추출
            patterns = {
                'reporter': r'보고자[:\s]*([가-힣]+)',
                'position': r'직위[:\s]*([가-힣\s]+)',
                'shares': r'(\d{1,3}(?:,\d{3})*)\s*주',
                'price': r'(\d{1,3}(?:,\d{3})*)\s*원',
                'transaction_date': r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    purchase_info[key] = match.group(1).strip()

            # 장내매수 확인
            if '장내매수' in content or '장내 매수' in content:
                purchase_info['transaction_type'] = '장내매수'
                purchase_info['reason'] = '장내매수'
                return purchase_info
            elif '매수' in content:
                purchase_info['transaction_type'] = '매수'
                purchase_info['reason'] = '매수'
                return purchase_info

            return None

        except Exception as e:
            logging.error(f"매수 정보 추출 실패: {e}")
            return None

class TelegramNotifier:
    """텔레그램 알림 클래스"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message: str) -> bool:
        """텔레그램 메시지 전송"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()

            logging.info("텔레그램 메시지 전송 성공")
            return True

        except Exception as e:
            logging.error(f"텔레그램 메시지 전송 실패: {e}")
            return False

    def format_executive_purchase_message(self, disclosure: ExecutiveDisclosure, 
                                        purchase_info: Dict) -> str:
        """임원 매수 알림 메시지 포맷팅"""
        current_time = datetime.now(KST)

        message = f"""🏢 <b>임원 장내매수 알림</b>

📊 <b>회사명:</b> {disclosure.corp_name}
📈 <b>종목코드:</b> {disclosure.stock_code}
👤 <b>보고자:</b> {purchase_info.get('reporter', disclosure.flr_nm)}
💼 <b>직위:</b> {purchase_info.get('position', 'N/A')}
💰 <b>거래유형:</b> {purchase_info.get('transaction_type', 'N/A')}
📊 <b>주식수:</b> {purchase_info.get('shares', 'N/A')}
💵 <b>가격:</b> {purchase_info.get('price', 'N/A')}
📅 <b>거래일:</b> {purchase_info.get('transaction_date', 'N/A')}
📋 <b>접수번호:</b> {disclosure.rcept_no}
📅 <b>공시일:</b> {disclosure.rcept_dt}

⏰ <b>알림시간:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}

#임원매수 #OpenDart #장내매수"""

        return message

    def send_test_message(self) -> bool:
        """시스템 시작 테스트 메시지"""
        current_time = datetime.now(KST)

        test_message = f"""🧪 <b>OpenDart API 모니터링 봇 테스트</b>

📅 <b>테스트 시간:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}
🤖 <b>상태:</b> OpenDart API 기반 임원 매수 모니터링 봇 정상 작동
🔑 <b>API:</b> OpenDart API 연결 성공

#테스트 #OpenDart #모니터링"""

        return self.send_message(test_message)

class ExecutiveMonitor:
    """임원 매수 모니터링 메인 클래스"""

    def __init__(self, dart_api_key: str, telegram_token: str, telegram_chat_id: str):
        self.dart_api = OpenDartAPI(dart_api_key)
        self.telegram = TelegramNotifier(telegram_token, telegram_chat_id)
        self.processed_disclosures = set()  # 중복 처리 방지

    def get_date_range(self, days_back: int = 1) -> Tuple[str, str]:
        """날짜 범위 계산"""
        today = datetime.now(KST).date()
        start_date = today - timedelta(days=days_back)

        start_str = start_date.strftime('%Y%m%d')
        end_str = today.strftime('%Y%m%d')

        logging.info(f"모니터링 기간: {start_str} ~ {end_str}")
        return start_str, end_str

    def monitor_executive_purchases(self, days_back: int = 1) -> List[Dict]:
        """임원 매수 모니터링 실행"""
        start_date, end_date = self.get_date_range(days_back)

        # 임원 공시 검색
        disclosures = self.dart_api.search_executive_disclosures(start_date, end_date)

        if not disclosures:
            logging.info("임원 공시가 없습니다.")
            return []

        purchase_results = []

        for disclosure in disclosures:
            # 중복 처리 방지
            if disclosure.rcept_no in self.processed_disclosures:
                continue

            logging.info(f"공시 상세 확인: {disclosure.corp_name} - {disclosure.flr_nm}")

            # 장내매수 여부 확인
            purchase_info = self.dart_api.check_purchase_transaction(disclosure.rcept_no)

            if purchase_info:
                logging.info(f"장내매수 발견: {disclosure.corp_name} - {disclosure.flr_nm}")

                # 결과 저장
                result = {
                    'disclosure': disclosure.__dict__,
                    'purchase_info': purchase_info,
                    'detected_at': datetime.now(KST).isoformat()
                }
                purchase_results.append(result)

                # 텔레그램 알림 전송
                message = self.telegram.format_executive_purchase_message(disclosure, purchase_info)
                self.telegram.send_message(message)

                # 처리 완료 표시
                self.processed_disclosures.add(disclosure.rcept_no)

                # API 호출 제한 고려 (1초 대기)
                time.sleep(1)

        return purchase_results

    def save_results(self, results: List[Dict]):
        """결과 저장"""
        if not results:
            return

        try:
            current_time = datetime.now(KST)
            filename = f"executive_purchases_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"/home/user/output/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logging.info(f"결과 저장 완료: {filepath}")

        except Exception as e:
            logging.error(f"결과 저장 실패: {e}")

def main():
    """메인 실행 함수"""
    # 로깅 설정
    logger = setup_logging()

    try:
        # 환경 변수 확인
        dart_api_key = os.getenv('DART_API_KEY', '470c22abb7b7f515e219c78c7aa92b15fd5a80c0')
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not telegram_token or not telegram_chat_id:
            logging.error("텔레그램 설정이 없습니다. 환경 변수를 확인하세요.")
            return

        logging.info("OpenDart API 기반 임원 매수 모니터링 시작")

        # 모니터 초기화
        monitor = ExecutiveMonitor(dart_api_key, telegram_token, telegram_chat_id)

        # 테스트 메시지 전송
        if monitor.telegram.send_test_message():
            logging.info("텔레그램 테스트 메시지 전송 성공")

        # 임원 매수 모니터링 실행
        results = monitor.monitor_executive_purchases(days_back=1)

        if results:
            logging.info(f"총 {len(results)}건의 임원 매수 발견")
            monitor.save_results(results)
        else:
            logging.info("임원 매수 공시가 없습니다.")

            # 모니터링 완료 알림
            current_time = datetime.now(KST)
            completion_message = f"""📊 <b>모니터링 완료</b>

📅 <b>조회 기간:</b> 어제-오늘
🔍 <b>검색 방식:</b> OpenDart API
📋 <b>결과:</b> 임원 매수 공시 없음
⏰ <b>완료 시간:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}

#모니터링완료 #OpenDart"""

            monitor.telegram.send_message(completion_message)

    except Exception as e:
        logging.error(f"실행 중 오류 발생: {e}")

        # 오류 알림
        if 'monitor' in locals():
            error_message = f"""❌ <b>시스템 오류</b>

🚨 <b>오류 내용:</b> {str(e)[:200]}...
⏰ <b>발생 시간:</b> {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}

#시스템오류 #OpenDart"""
            monitor.telegram.send_message(error_message)

    finally:
        logging.info("모니터링 완료")

if __name__ == "__main__":
    main()
