import {
  apiMessage,
  init_api_service
} from "./chunk-ISXBJMET.js";
import "./chunk-AAMV5SOX.js";

// src/app/core/api.service.spec.ts
init_api_service();
describe("apiMessage", () => {
  it("reads a string detail from the API", () => {
    expect(apiMessage({ error: { detail: "Customer not found" } })).toBe("Customer not found");
  });
  it("joins field validation messages", () => {
    expect(apiMessage({ error: { detail: [{ msg: "Enter a mobile number" }, { msg: "Name is too short" }] } })).toBe("Enter a mobile number Name is too short");
  });
  it("uses a plain message when the response has no detail", () => {
    expect(apiMessage({})).toBe("Something went wrong. Please try again.");
  });
});
//# sourceMappingURL=spec-api.service.spec.js.map
