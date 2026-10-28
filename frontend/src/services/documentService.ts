export function documentStatus(status: string) {
  return ({queued: '처리 대기', processing: '전처리·색인 중', parsing: '전처리 중', embedding: '임베딩 중',
    indexing: '색인 중', ready: '사용 가능', partial: '부분 사용 가능', failed: '처리 실패', inactive: '비활성',
    superseded: '새 판본으로 대체됨', pending: '대기', running: '처리 중', succeeded: '완료', cancelled: '취소됨'} as Record<string, string>)[status] || status;
}
