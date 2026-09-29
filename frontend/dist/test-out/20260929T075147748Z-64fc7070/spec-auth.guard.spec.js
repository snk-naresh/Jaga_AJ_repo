import {
  AuthService,
  Router,
  UrlTree,
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
import {
  init_core,
  inject
} from "./chunk-AAMV5SOX.js";

// src/app/core/auth.guard.spec.ts
init_testing();
init_http();
init_router();

// src/app/core/auth.guard.ts
init_router();
init_core();
init_auth_service();
var authGuard = () => {
  const a = inject(AuthService);
  return a.isLoggedIn() || inject(Router).createUrlTree(["/login"]);
};

// src/app/core/auth.guard.spec.ts
describe("authGuard", () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideRouter([])]
    });
  });
  afterEach(() => localStorage.clear());
  it("sends a signed-out visitor to the login page", () => {
    const result = TestBed.runInInjectionContext(() => authGuard({}, {}));
    const router = TestBed.inject(Router);
    expect(result).toBeInstanceOf(UrlTree);
    expect(router.serializeUrl(result)).toBe("/login");
  });
  it("allows a signed-in staff member through", () => {
    localStorage.setItem("token", "header.payload.sig");
    const result = TestBed.runInInjectionContext(() => authGuard({}, {}));
    expect(result).toBe(true);
  });
});
//# sourceMappingURL=spec-auth.guard.spec.js.map
