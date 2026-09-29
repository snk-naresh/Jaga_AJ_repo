import {
  HttpTestingController,
  init_testing as init_testing2,
  provideHttpClientTesting
} from "./chunk-XBFNM46A.js";
import {
  AuthService,
  Router,
  init_auth_service,
  init_router,
  provideRouter
} from "./chunk-Y44LDZDY.js";
import {
  init_http,
  provideHttpClient
} from "./chunk-ISXBJMET.js";
import {
  TestBed,
  init_testing
} from "./chunk-5FII7YQZ.js";
import "./chunk-AAMV5SOX.js";

// src/app/core/auth.service.spec.ts
init_testing();
init_http();
init_testing2();
init_router();
init_auth_service();
function token(role) {
  const payload = btoa(JSON.stringify({ role }));
  return `header.${payload}.sig`;
}
describe("AuthService", () => {
  let auth;
  let http;
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([{ path: "login", children: [] }])]
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    http.verify();
    localStorage.clear();
  });
  it("stores the token after a successful login", () => {
    auth.login("admin", "secret").subscribe();
    http.expectOne("/api/auth/login").flush({ access_token: token("ADMIN") });
    expect(auth.isLoggedIn()).toBe(true);
    expect(auth.role()).toBe("ADMIN");
  });
  it("clears the session and opens the sign-in page", () => {
    localStorage.setItem("token", token("STAFF"));
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, "navigateByUrl");
    auth.logout();
    expect(auth.isLoggedIn()).toBe(false);
    expect(navigate).toHaveBeenCalledWith("/login");
  });
});
//# sourceMappingURL=spec-auth.service.spec.js.map
