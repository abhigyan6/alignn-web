import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import vm from "node:vm";

import { expect, test } from "@playwright/test";
import * as ts from "typescript";

type Environment = Record<string, string | undefined>;
type ConfigResult = {
  client: { isClerkPublishableKeyConfigured: boolean };
  server: { isClerkServerConfigured: boolean; publicOrigin: string };
};

const PUBLIC_KEY = "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY";
const SECRET_KEY = "CLERK_SECRET_KEY";
const ORIGIN_KEY = "PUBLIC_ORIGIN";
const syntheticPublic = "synthetic-public-value";
const syntheticPrivate = "synthetic-private-value";

// Resolve from the web workspace whether run from it or from the repo root.
const webRoot = existsSync(join(process.cwd(), "src"))
  ? process.cwd()
  : join(process.cwd(), "apps", "web");

function readSource(relativePath: string): string {
  const path = join(webRoot, relativePath);
  expect(existsSync(path), `${relativePath} must exist`).toBe(true);
  return readFileSync(path, "utf8");
}

function parse(relativePath: string): ts.SourceFile {
  return ts.createSourceFile(
    relativePath,
    readSource(relativePath),
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TS,
  );
}

/** Evaluates the real production source in a fresh VM with a synthetic env. */
function evaluateConfig(environment: Environment): ConfigResult {
  const env: Environment = { ...environment };
  for (const key of Object.keys(env)) {
    if (env[key] === undefined) delete env[key];
  }
  const sandbox = { process: { env } };
  const cache = new Map<string, Record<string, unknown>>();

  function load(name: "client" | "server"): Record<string, unknown> {
    const cached = cache.get(name);
    if (cached) return cached;
    const { outputText } = ts.transpileModule(
      readSource(`src/lib/config/${name}.ts`),
      {
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          target: ts.ScriptTarget.ES2022,
        },
      },
    );
    const exports: Record<string, unknown> = {};
    const require = (specifier: string): unknown => {
      if (specifier === "server-only") return {};
      if (specifier === "./client") {
        return load("client");
      }
      throw new Error(`Unexpected import in ${name} config: ${specifier}`);
    };
    const context = vm.createContext({ ...sandbox, exports, require });
    vm.runInContext(outputText, context, { filename: `${name}.ts` });
    cache.set(name, exports);
    return exports;
  }

  const client = load("client");
  const server = load("server");
  return {
    client: {
      isClerkPublishableKeyConfigured:
        client.isClerkPublishableKeyConfigured as boolean,
    },
    server: {
      isClerkServerConfigured: server.isClerkServerConfigured as boolean,
      publicOrigin: server.publicOrigin as string,
    },
  };
}

function moduleSpecifiers(file: ts.SourceFile): string[] {
  const specifiers: string[] = [];
  for (const statement of file.statements) {
    if (
      (ts.isImportDeclaration(statement) ||
        ts.isExportDeclaration(statement)) &&
      statement.moduleSpecifier &&
      ts.isStringLiteral(statement.moduleSpecifier)
    ) {
      specifiers.push(statement.moduleSpecifier.text);
    }
  }
  return specifiers;
}

function exportedNames(file: ts.SourceFile): string[] {
  const names: string[] = [];
  const hasExport = (statement: ts.Statement): boolean =>
    ts.canHaveModifiers(statement) &&
    (ts.getModifiers(statement) ?? []).some(
      (m) => m.kind === ts.SyntaxKind.ExportKeyword,
    );
  for (const statement of file.statements) {
    if (ts.isVariableStatement(statement)) {
      if (hasExport(statement)) {
        for (const declaration of statement.declarationList.declarations) {
          names.push(declaration.name.getText(file));
        }
      }
    } else if (
      ts.isExportDeclaration(statement) ||
      ts.isExportAssignment(statement)
    ) {
      names.push("<re-export>");
    } else if (hasExport(statement)) {
      names.push("<other-export>");
    }
  }
  return names;
}

/** Every name or string that refers to a variable, found by walking the AST. */
function referencedNames(file: ts.SourceFile): Set<string> {
  const names = new Set<string>();
  const visit = (node: ts.Node): void => {
    if (ts.isIdentifier(node)) names.add(node.text);
    if (ts.isStringLiteralLike(node)) names.add(node.text);
    ts.forEachChild(node, visit);
  };
  visit(file);
  return names;
}

/** Names read through `process.env.NAME` or `process.env["NAME"]`. */
function literalEnvReads(file: ts.SourceFile): string[] {
  const reads: string[] = [];
  const isProcessEnv = (node: ts.Expression): boolean =>
    ts.isPropertyAccessExpression(node) &&
    ts.isIdentifier(node.expression) &&
    node.expression.text === "process" &&
    node.name.text === "env";
  const visit = (node: ts.Node): void => {
    if (ts.isPropertyAccessExpression(node) && isProcessEnv(node.expression)) {
      reads.push(node.name.text);
    } else if (
      ts.isElementAccessExpression(node) &&
      isProcessEnv(node.expression) &&
      ts.isStringLiteralLike(node.argumentExpression)
    ) {
      reads.push(node.argumentExpression.text);
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return reads;
}

test("public configuration follows publishable-key presence", () => {
  expect(evaluateConfig({}).client.isClerkPublishableKeyConfigured).toBe(false);
  expect(
    evaluateConfig({ [PUBLIC_KEY]: "" }).client.isClerkPublishableKeyConfigured,
  ).toBe(false);
  expect(
    evaluateConfig({ [PUBLIC_KEY]: syntheticPublic }).client
      .isClerkPublishableKeyConfigured,
  ).toBe(true);
  expect(exportedNames(parse("src/lib/config/client.ts"))).toEqual([
    "isClerkPublishableKeyConfigured",
  ]);
});

test("server configuration requires both settings", () => {
  const cases: Array<[Environment, boolean, boolean]> = [
    [{}, false, false],
    [{ [PUBLIC_KEY]: syntheticPublic }, false, true],
    [{ [PUBLIC_KEY]: syntheticPublic, [SECRET_KEY]: "" }, false, true],
    [{ [SECRET_KEY]: syntheticPrivate }, false, false],
    [
      { [PUBLIC_KEY]: syntheticPublic, [SECRET_KEY]: syntheticPrivate },
      true,
      true,
    ],
  ];
  for (const [environment, server, client] of cases) {
    const result = evaluateConfig(environment);
    expect(result.server.isClerkServerConfigured).toBe(server);
    expect(result.client.isClerkPublishableKeyConfigured).toBe(client);
  }
  expect(exportedNames(parse("src/lib/config/server.ts")).sort()).toEqual([
    "isClerkServerConfigured",
    "publicOrigin",
  ]);
});

test("origin preserves explicit missing and empty values", () => {
  expect(
    evaluateConfig({ [ORIGIN_KEY]: "https://alignn.test" }).server.publicOrigin,
  ).toBe("https://alignn.test");
  expect(evaluateConfig({}).server.publicOrigin).toBe("http://localhost:3000");
  expect(evaluateConfig({ [ORIGIN_KEY]: "" }).server.publicOrigin).toBe("");
});

test("configuration respects client and server boundaries", () => {
  const client = parse("src/lib/config/client.ts");
  const server = parse("src/lib/config/server.ts");

  // Client config: literal public lookup only, nothing private, no imports.
  expect(literalEnvReads(client)).toEqual([PUBLIC_KEY]);
  const clientNames = referencedNames(client);
  for (const privateName of [SECRET_KEY, ORIGIN_KEY, "server-only"]) {
    expect(clientNames.has(privateName), `client mentions ${privateName}`).toBe(
      false,
    );
  }
  expect(moduleSpecifiers(client)).toEqual([]);

  // Server config: starts with the side-effect-only server marker import.
  const first = server.statements[0];
  expect(
    first &&
      ts.isImportDeclaration(first) &&
      !first.importClause &&
      ts.isStringLiteral(first.moduleSpecifier) &&
      first.moduleSpecifier.text,
  ).toBe("server-only");
  expect(moduleSpecifiers(server).sort()).toEqual(["./client", "server-only"]);
  const clientImport = server.statements.find(
    (s): s is ts.ImportDeclaration =>
      ts.isImportDeclaration(s) &&
      ts.isStringLiteral(s.moduleSpecifier) &&
      s.moduleSpecifier.text === "./client",
  );
  const clientBindings = clientImport?.importClause?.namedBindings;
  expect(
    clientBindings &&
      ts.isNamedImports(clientBindings) &&
      clientBindings.elements.map((e) => e.name.text),
  ).toEqual(["isClerkPublishableKeyConfigured"]);
  expect(
    literalEnvReads(server).filter(
      (n) => ![PUBLIC_KEY, SECRET_KEY, ORIGIN_KEY].includes(n),
    ),
  ).toEqual([]);

  // Consumers import the module matching their runtime.
  const consumers: Array<[string, string]> = [
    ["src/app/layout.tsx", "@/lib/config/client"],
    ["src/proxy.ts", "@/lib/config/server"],
    ["src/app/login/[[...login]]/page.tsx", "@/lib/config/server"],
    ["src/app/signup/[[...signup]]/page.tsx", "@/lib/config/server"],
    ["src/app/onboarding/page.tsx", "@/lib/config/server"],
    ["src/app/workspace/page.tsx", "@/lib/config/server"],
  ];
  for (const [path, expected] of consumers) {
    const specifiers = moduleSpecifiers(parse(path));
    expect(specifiers, `${path} imports ${expected}`).toContain(expected);
    expect(specifiers, `${path} must not use legacy config`).not.toContain(
      "@/lib/config",
    );
    const other =
      expected === "@/lib/config/client"
        ? "@/lib/config/server"
        : "@/lib/config/client";
    expect(specifiers, `${path} must not import ${other}`).not.toContain(other);
  }
});
