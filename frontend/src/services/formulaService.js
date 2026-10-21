/**
 * [계층 3] KaTeX Mathematical Formula Service
 * React에 비의존적인 순수 수식 렌더링 및 LaTeX 파싱 서비스
 */

import katex from 'katex';

export const formulaService = {
  /**
   * LaTeX 수식 문자열을 KaTeX HTML 블록으로 변환
   * @param {string} formula - LaTeX 수식 (예: "F_{\\text{bonding}} = P \\times A")
   * @param {boolean} [displayMode=true] - 블록 수식 여부
   * @returns {string} 안전한 KaTeX 렌더링 HTML 문자열
   */
  renderFormula(formula, displayMode = true) {
    if (!formula || typeof formula !== 'string') return '';
    try {
      return katex.renderToString(formula.trim(), {
        displayMode,
        throwOnError: false,
        output: 'htmlAndMathml'
      });
    } catch (e) {
      console.warn('KaTeX render error:', e);
      return `<code class="katex-fallback">${formula}</code>`;
    }
  },

  /**
   * 텍스트 내 inline 수식 ($...$) 및 display 수식 ($$...$$) 자동 파싱
   * @param {string} text
   * @returns {string}
   */
  renderTextWithMath(text) {
    if (!text || typeof text !== 'string') return '';

    // 1. Display Math: $$...$$
    let processed = text.replace(/\$\$([^$]+)\$\$/g, (_, math) => {
      return `<div class="katex-display-wrapper">${this.renderFormula(math, true)}</div>`;
    });

    // 2. Inline Math: $...$
    processed = processed.replace(/\$([^$]+)\$/g, (_, math) => {
      return `<span class="katex-inline-wrapper">${this.renderFormula(math, false)}</span>`;
    });

    return processed;
  }
};
