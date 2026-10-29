import { documentWikiRepository } from '../repositories/documentWikiRepository';
export const loadDocumentWikiNotice = documentWikiRepository.get;
export function documentWikiLabel(status: string): string {
  return ({disabled: '자동 위키 검토 꺼짐', paused: '자동 검토 일시 중지', not_scheduled: '기존 자료는 자동 소급 검토하지 않습니다', waiting: '사용 가능한 새 문헌 판본을 기다리는 중',
    pending: '위키 보강점 확인 대기', running: '위키 보강점 확인 중', budget_wait: '일일 자동 검토 한도로 대기 중',
    succeeded: '위키 보강점 확인 완료', no_changes: '추가로 제안할 내용 없음', failed: '위키 자동 검토 실패',
    superseded: '문헌 판본 변경으로 이전 검토 종료'} as Record<string, string>)[status] || status;
}
