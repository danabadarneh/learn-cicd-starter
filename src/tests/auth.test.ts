// src/tests/auth.test.ts
import { describe, test, expect } from "vitest";
import { getAPIKey } from "../api/auth";

describe("getAPIKey", () => {
  test("should return a key", () => {
    const key = getAPIKey();
    expect(key).toBe("MY_REAL_KEY"); // لازم يطابق القيمة في auth.ts
  });
});
