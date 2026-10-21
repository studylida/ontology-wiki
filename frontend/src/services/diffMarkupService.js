/**
 * [계층 3] DiffMarkupService
 * 원본과 개정본 간의 문장 단위 Diff 분석 및 <mark class="diff-added"> 마크업 합성
 */

export const diffMarkupService = {
  /**
   * 텍스트를 문장/단락 단위로 분할하여 Diff 마크업 생성
   * @param {string} oldText
   * @param {string} newText
   * @returns {string} HTML 마크업 문자열
   */
  generateDiffHtml(oldText = '', newText = '') {
    if (!oldText && !newText) return '';
    if (!oldText) return `<mark class="diff-added">${this.escapeHtml(newText)}</mark>`;
    if (!newText) return `<del class="diff-removed">${this.escapeHtml(oldText)}</del>`;

    const oldLines = oldText.split('\n');
    const newLines = newText.split('\n');

    const result = [];
    const maxLen = Math.max(oldLines.length, newLines.length);

    for (let i = 0; i < maxLen; i++) {
      const o = oldLines[i];
      const n = newLines[i];

      if (o === undefined) {
        result.push(`<div class="diff-line added"><mark class="diff-added">+ ${this.escapeHtml(n)}</mark></div>`);
      } else if (n === undefined) {
        result.push(`<div class="diff-line removed"><del class="diff-removed">- ${this.escapeHtml(o)}</del></div>`);
      } else if (o === n) {
        result.push(`<div class="diff-line unchanged">${this.escapeHtml(n)}</div>`);
      } else {
        result.push(
          `<div class="diff-line modified">` +
            `<del class="diff-removed">- ${this.escapeHtml(o)}</del><br/>` +
            `<mark class="diff-added">+ ${this.escapeHtml(n)}</mark>` +
          `</div>`
        );
      }
    }

    return result.join('\n');
  },

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
};
