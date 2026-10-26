/** Follow the arriving answer text, not citation cards that may arrive before it. */
export function replyFollowScrollTop(
  container: HTMLElement,
  messageId?: string,
): number {
  const maximum = Math.max(0, container.scrollHeight - container.clientHeight);
  const message = messageId
    ? container.ownerDocument.getElementById(`message-${messageId}`)
    : null;
  if (!message || !container.contains(message)) return maximum;
  const text = Array.from(
    message.querySelectorAll<HTMLElement>(
      ".answer-body > .markdown, .answer-body > .answer-section > .markdown",
    ),
  )
    .filter((element) => element.textContent?.trim())
    .at(-1);
  const anchor =
    text ||
    message.querySelector<HTMLElement>(".awaiting-answer") ||
    message.querySelector<HTMLElement>(".message-header") ||
    message;
  const bottom =
    anchor.getBoundingClientRect().bottom -
    container.getBoundingClientRect().top +
    container.scrollTop;
  return Math.max(0, Math.min(maximum, bottom - container.clientHeight + 64));
}
