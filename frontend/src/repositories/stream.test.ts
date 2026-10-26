import { describe, expect, it } from "vitest";
import { parseRunEvent, SseParser } from "./stream";

describe("authenticated SSE framing", () => {
  it("handles data split across network reads and CRLF frame boundaries", () => {
    const parser = new SseParser();
    expect(
      parser.push(": heartbeat\r\nid: 1\r\nevent: text.delta\r\nda"),
    ).toEqual([]);
    expect(
      parser.push(
        'ta: {"type":"text.delta","runId":"r1","seq":1,"at":"now","data":{"text":"한글"}}\r',
      ),
    ).toEqual([]);
    const frames = parser.push("\n\r\n");
    expect(frames).toHaveLength(1);
    expect(parseRunEvent(frames[0]).data.text).toBe("한글");
  });
  it("joins multiline data and ignores comments without manufacturing an event", () => {
    const parser = new SseParser();
    expect(parser.push(": ping\n\n")).toEqual([]);
    expect(
      parser.push(
        'data: {"type":"run.started",\ndata: "runId":"r","seq":1,"at":"now","data":{}}\n\n',
      ),
    ).toHaveLength(1);
  });
  it("refuses invented events and invalid sequence values", () => {
    expect(() =>
      parseRunEvent('{"type":"usage.updated","runId":"r","seq":1,"data":{}}'),
    ).toThrow();
    expect(() =>
      parseRunEvent('{"type":"text.delta","runId":"r","seq":0,"data":{}}'),
    ).toThrow();
  });
});
