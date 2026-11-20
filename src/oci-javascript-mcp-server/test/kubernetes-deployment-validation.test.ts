/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { getEventListeners, once } from "node:events";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer, type IncomingHttpHeaders } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { registerHooks } from "node:module";
import test, { type TestContext } from "node:test";
import { loadAllYaml, type V1Node, type V1Namespace } from "@kubernetes/client-node";
import { buildExecutionPod } from "../src/isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import type { KubernetesPod, ResourceAttributes } from "../src/isolation/kubernetes-api.ts";
import {
  createKubeconfigValidationApi,
  main,
  parseValidationOptions,
  validateDeployment,
  type AdmissionProbeResult,
  type DeploymentInspectionApi,
  type DeploymentValidationApi
} from "../src/kubernetes-deployment-validation.ts";
import { conformingPodAdmission, validInClusterEnvironment, validKataEnvironment, validLocalEnvironment } from "./kata-fixtures.ts";

const args = ["--kubeconfig", "/tmp/deployment-validation-config", "--context", "target"];
const hostArgs = [...args, "--host-service-account", "oci-js-host", "--impersonate", "--inspection-context", "target"];

test("deployment validation rejects a fail-open policy before submitting pod probes", async () => {
  const api = new ValidationApi("in-cluster");
  const policy = referenceAdmission("in-cluster", "ValidatingAdmissionPolicy");
  policy.spec.failurePolicy = "Ignore";
  Object.assign(api, { inspection: {
    identity: async () => ({ username: "deployment-reader", groups: [] }),
    readPolicy: async () => policy,
    readBinding: async () => referenceAdmission("in-cluster", "ValidatingAdmissionPolicyBinding")
  } });
  const report = await validateDeployment(parseValidationOptions(hostArgs, validInClusterEnvironment()), api);
  assert.equal(report.passed, false);
  assert.equal(api.pods.length, 0);
  assert.equal(report.checks.find(check => check.id === "deployment:admission")?.outcome, "failed");
});

test("Kata validation rejects a RuntimeClass that can schedule outside the reviewed pool", async () => {
  const api = new ValidationApi("kata-in-cluster");
  api.runtime.scheduling = undefined;
  const report = await validateDeployment(parseValidationOptions(hostArgs, validKataEnvironment()), api);
  assert.equal(report.passed, false);
  assert.equal(api.pods.length, 0);
  assert.equal(report.checks.find(check => check.id === "deployment:runtime-class")?.outcome, "failed");
});

test("Kata validation probes environment sources and rejects a permissive trusted-host placement policy", async () => {
  const api = new ValidationApi("kata-in-cluster");
  Object.assign(api.inspection, { dryRunCreatePod: async () => ({ outcome: "accepted" as const }) });
  const report = await validateDeployment(parseValidationOptions(hostArgs, validKataEnvironment()), api);
  assert.equal(report.passed, false);
  assert(api.pods.some(pod => pod.spec!.containers[0]!.envFrom?.[0]?.configMapRef?.name === "unsafe-environment"));
  assert.equal(report.checks.find(check => check.id === "admission:trusted-host:pool")?.outcome, "failed");
});

function referenceAdmission(profile: string, kind: string, host = false): any {
  const path = profile === "kata-in-cluster" ? "examples/kata-kubernetes/v1/06-admission-policy.yaml"
    : "examples/kubernetes/v1/standard-in-cluster.yaml";
  return structuredClone(loadAllYaml(readFileSync(path, "utf8")).find((item: any) =>
    item.kind === kind && item.metadata.name.includes(host ? "trusted-host-placement" : "execution-pods")));
}

test("deployment validation keeps target profiles separate from connection credentials", () => {
  for (const environment of [validInClusterEnvironment(), validKataEnvironment()]) {
    delete environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME;
    delete environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID;
    const before = { ...environment };
    const options = parseValidationOptions(hostArgs, environment);
    assert.equal(options.config.profile, environment.OCI_JAVASCRIPT_KUBERNETES_PROFILE);
    assert.equal(options.kubeconfigPath, "/tmp/deployment-validation-config");
    assert.equal(options.expectedIdentity, "system:serviceaccount:oci-js-host:oci-js-host");
    assert.equal(options.impersonate, true);
    assert.equal(options.probeMetadata, "synthetic-host-identity");
    assert.deepEqual(environment, before);
  }
  const local = parseValidationOptions(args, validLocalEnvironment());
  assert.equal(local.config.profile, "local-development");
  assert.equal(local.expectedIdentity, undefined);
  assert.equal(local.config.credentialMode === "explicit-kubeconfig" && local.config.kubeconfigContext, "target");
});

test("inspection requires explicit credentials and validates configured policy and pool names", () => {
  assert.throws(() => parseValidationOptions([...args, "--host-service-account", "host"], validInClusterEnvironment()), /inspection-context/);
  assert.throws(() => parseValidationOptions([...args, "--inspection-context", "target"], validLocalEnvironment()), /in-cluster/);
  assert.throws(() => parseValidationOptions([...hostArgs, "--kata-profile", "other"], validInClusterEnvironment()), /kata-in-cluster/);
  for (const flag of ["--admission-policy", "--admission-binding", "--host-placement-policy", "--host-placement-binding", "--kata-profile", "--execution-pool", "--trusted-host-pool"]) {
    assert.throws(() => parseValidationOptions([...hostArgs, flag, "Invalid_Name"], validKataEnvironment()), /DNS/);
  }
  assert.throws(() => parseValidationOptions([...hostArgs, "--execution-pool", "x".repeat(64)], validKataEnvironment()), /63/);
  assert.throws(() => parseValidationOptions([...hostArgs, "--execution-pool", "same", "--trusted-host-pool", "same"], validKataEnvironment()), /differ/);
  const custom = parseValidationOptions([...hostArgs, "--admission-policy", "custom-policy", "--host-placement-policy", "custom-host",
    "--kata-profile", "custom-profile", "--execution-pool", "exec-pool", "--trusted-host-pool", "host-pool"], validKataEnvironment());
  assert.equal(custom.admissionBinding, "custom-policy");
  assert.equal(custom.hostPlacementBinding, "custom-host");
  assert.equal(custom.kataProfile, "custom-profile");
});

test("missing inspection, weak namespace labels, mismatched object identities and empty node pools fail before probes", async () => {
  const cases: Array<[string, (api: ValidationApi) => void, string]> = [
    ["inspection", api => { Object.assign(api, { inspection: undefined }); }, "deployment:inspection-identity"],
    ["reader identity", api => { api.inspection.identity = async () => ({ username: "", groups: [] }); }, "deployment:inspection-identity"],
    ["namespace", api => { api.readNamespace = async name => ({ metadata: { name, labels: {} } }); }, "namespace"],
    ["runtime identity", api => { api.runtime.metadata!.name = "wrong-runtime"; }, "deployment:runtime-class"],
    ["binding identity", api => { api.inspection.readBinding = async () => ({ ...referenceAdmission("kata-in-cluster", "ValidatingAdmissionPolicyBinding"), metadata: { name: "wrong" } }); }, "deployment:admission"],
    ["host namespace", api => { api.inspection.readNamespace = async name => ({ metadata: { name, labels: {} } }); }, "deployment:trusted-host-namespace"],
    ["nodes", api => { api.inspection.listNodes = async () => []; }, "deployment:node-pools"]
  ];
  for (const [name, mutate, expected] of cases) {
    const api = new ValidationApi("kata-in-cluster");
    mutate(api);
    const report = await validateDeployment(parseValidationOptions(hostArgs, validKataEnvironment()), api);
    assert.equal(report.passed, false, name);
    assert.equal(api.pods.length, 0, name);
    assert.equal(report.checks.find(check => check.id === expected)?.outcome, "failed", name);
  }
});

test("cancellation of policy inspection cannot issue a late binding read or mutate returned evidence", async () => {
  const api = new ValidationApi("in-cluster");
  let resolvePolicy!: (value: any) => void;
  let signal!: AbortSignal;
  api.inspection.readPolicy = async (_name: string, incoming?: AbortSignal) => {
    signal = incoming!;
    return await new Promise(resolve => { resolvePolicy = resolve; });
  };
  let bindings = 0;
  api.inspection.readBinding = async () => { bindings++; return referenceAdmission("in-cluster", "ValidatingAdmissionPolicyBinding"); };
  const report = await validateDeployment({ ...parseValidationOptions(hostArgs, validInClusterEnvironment()), timeoutMs: 10 }, api);
  assert.equal(report.passed, false);
  assert.equal(signal.aborted, true);
  const snapshot = JSON.stringify(report);
  resolvePolicy(referenceAdmission("in-cluster", "ValidatingAdmissionPolicy"));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(bindings, 0);
  assert.equal(JSON.stringify(report), snapshot);
});

test("validation rejects ambiguous credentials, incomplete identity, and invalid timeouts", () => {
  for (const invalid of [[], ["--kubeconfig", "x"], [...args, "--unknown"],
    [...hostArgs, "--timeout-seconds", "0"], [...hostArgs, "--timeout-seconds", "301"],
    [...hostArgs, "--timeout-seconds", "1.5"], [...args, "--host-service-account", "Bad_Name"]]) {
    assert.throws(() => parseValidationOptions(invalid, validInClusterEnvironment()));
  }
  assert.throws(() => parseValidationOptions(args, validInClusterEnvironment()), /host-service-account/);
  assert.throws(() => parseValidationOptions([...args, "--impersonate"], validLocalEnvironment()), /in-cluster/);
  const incompatible = { ...validInClusterEnvironment(), OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG: "/tmp/config" };
  assert.throws(() => parseValidationOptions(hostArgs, incompatible), /incompatible/);
  assert.throws(() => parseValidationOptions(hostArgs, {
    ...validInClusterEnvironment(), OCI_JAVASCRIPT_ISOLATION_PROVIDER: "podman"
  }), /kubernetes/);
  assert.doesNotThrow(() => parseValidationOptions([
    ...args, "--host-service-account", "host.account", "--inspection-context", "target"
  ], validInClusterEnvironment()));
});

test("in-cluster validation requires the intended username and exact service-account groups", async () => {
  const options = parseValidationOptions(args.concat("--host-service-account", "oci-js-host", "--inspection-context", "target"), validInClusterEnvironment());
  for (const groups of [[], ["system:authenticated"], [...hostGroups, "system:masters"]]) {
    const api = new ValidationApi("in-cluster");
    api.groups = groups;
    const report = await validateDeployment(options, api);
    assert.equal(report.passed, false);
    assert.equal(api.pods.length, 0);
  }
  const api = new ValidationApi("in-cluster");
  const report = await validateDeployment(options, api);
  assert.equal(report.passed, true);
  assert.deepEqual(report.identity, { username: options.expectedIdentity, groups: hostGroups });
});

test("standard and Kata validation dry-run every reviewed variant without executing or deleting pods", async () => {
  for (const environment of [validInClusterEnvironment(), validKataEnvironment()]) {
    const options = parseValidationOptions(hostArgs, environment);
    const api = new ValidationApi(options.config.profile);
    const report = await validateDeployment(options, api);
    assert.equal(report.passed, true);
    assert.equal(report.identity?.username, options.expectedIdentity);
    assert.equal(api.pods.length, options.config.profile === "kata-in-cluster" ? 93 : 72);
    assert.equal(api.runtimeReads, options.config.profile === "kata-in-cluster" ? 1 : 0);
    assert.equal(api.permissions.length, options.config.profile === "kata-in-cluster" ? 11 : 10);
    assert.equal(api.pods[0]?.spec?.runtimeClassName, options.config.profile === "kata-in-cluster" ? "kata-qemu-runtime-rs" : undefined);
  }
});

test("an accepted negative probe fails even for local development and all variants are reported", async () => {
  const options = parseValidationOptions(args, validLocalEnvironment());
  const api = new ValidationApi("local-development");
  api.acceptAll = true;
  const report = await validateDeployment(options, api);
  assert.equal(report.passed, false);
  assert.equal(api.pods.length, 61);
  assert.equal(report.checks.filter(check => check.outcome === "failed").length, 60);
  assert.equal(report.checks.find(check => check.id === "admission:image")?.outcome, "failed");
});

test("identity, authorization, RuntimeClass and positive-probe failures stop negative probes", async () => {
  const options = parseValidationOptions(hostArgs, validKataEnvironment());
  for (const fault of ["identity", "permission", "runtime", "conforming", "api"] as const) {
    const api = new ValidationApi("kata-in-cluster");
    api.fault = fault;
    const report = await validateDeployment(options, api);
    assert.equal(report.passed, false, fault);
    assert(api.pods.length <= 1, fault);
    assert.equal(JSON.stringify(report).includes("secret cluster endpoint"), false);
  }
});

test("a transient negative-probe API error is failure, not evidence of rejection", async () => {
  const api = new ValidationApi("in-cluster");
  api.negativeError = true;
  const report = await validateDeployment(parseValidationOptions(hostArgs, validInClusterEnvironment()), api);
  assert.equal(report.passed, false);
  assert.equal(report.checks.find(check => check.id === "admission:metadata-owner-reference")?.statusCode, 503);
  assert.equal(JSON.stringify(report).includes("secret cluster endpoint"), false);
});

test("cancellation bounds a hung API call and stops further requests", { timeout: 2000 }, async () => {
  const controller = new AbortController();
  const api = new ValidationApi("in-cluster");
  api.identity = async signal => {
    assert.equal(signal.aborted, false);
    setTimeout(() => controller.abort(), 10);
    return await new Promise<{ username: string; groups: string[] }>(() => undefined);
  };
  const report = await validateDeployment(parseValidationOptions(hostArgs, validInClusterEnvironment()), api, controller.signal);
  assert.equal(report.passed, false);
  assert.equal(api.pods.length, 0);
  assert.equal(report.checks[0]?.detail, "Validation cancelled or timed out");
});

test("CLI provides help, JSON, nonzero failures and sanitized setup errors", async () => {
  const output: string[] = [];
  const write = (text: string) => { output.push(text); };
  assert.equal(await main(["--help"], {}, { write }), 0);
  assert.match(output.pop()!, /--kubeconfig/);
  assert.equal(await main([...hostArgs, "--json"], validInClusterEnvironment(), {
    write, api: new ValidationApi("in-cluster")
  }), 0);
  assert.equal(JSON.parse(output.pop()!).passed, true);
  const failing = new ValidationApi("in-cluster");
  failing.acceptAll = true;
  assert.equal(await main(hostArgs, validInClusterEnvironment(), { write, api: failing }), 1);
  assert.match(output.pop()!, /FAIL/);
  assert.equal(await main([], {}, { write }), 1);
  assert.match(output.pop()!, /kubeconfig/);
  assert.equal(await main(hostArgs, validInClusterEnvironment(), { write }), 1);
  assert.doesNotMatch(output.pop()!, /ENOENT|secret|stack/);
});

test("kubeconfig adapter requires an explicit existing context and configures impersonation on every API", async t => {
  const directory = mkdtempSync(join(tmpdir(), "oci-js-validation-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const kubeconfigPath = join(directory, "config");
  writeFileSync(kubeconfigPath, JSON.stringify({
    apiVersion: "v1", kind: "Config",
    clusters: [{ name: "cluster", cluster: { server: "https://cluster.invalid" } }],
    users: [{ name: "operator", user: { token: "secret-test-token" } }],
    contexts: [{ name: "target", context: { cluster: "cluster", user: "operator" } }],
    "current-context": "not-selected"
  }));
  const options = parseValidationOptions(["--kubeconfig", kubeconfigPath, "--context", "absent", "--host-service-account", "oci-js-host", "--inspection-context", "target"], validInClusterEnvironment());
  assert.throws(() => createKubeconfigValidationApi(options), /context/);
});

test("real SDK uses the explicit context and host impersonation for every dry-run/review", async t => {
  for (const profile of ["in-cluster", "kata-in-cluster"] as const) {
    const fixture = await fakeApi(t, profile);
    const original = readFileSync(fixture.options.kubeconfigPath, "utf8");
    const report = await validateDeployment(fixture.options, createKubeconfigValidationApi(fixture.options));
    assert.equal(report.passed, true, JSON.stringify(report.checks.filter(check => check.outcome === "failed")));
    assert.equal(readFileSync(fixture.options.kubeconfigPath, "utf8"), original);
    for (const request of fixture.requests) {
      const isInspection = request.url.pathname.includes("admissionregistration.k8s.io")
        || request.url.pathname === "/api/v1/nodes"
        || request.url.pathname.endsWith("/namespaces/oci-js-host")
        || request.url.pathname.includes("/namespaces/oci-js-host/")
        || (request.url.pathname.endsWith("selfsubjectreviews") && request.headers["impersonate-user"] === undefined);
      assert.equal(request.headers["impersonate-user"], isInspection ? undefined : fixture.options.expectedIdentity);
      assert.equal(request.headers.authorization, "Bearer secret-test-token");
      assert.equal(request.headers["impersonate-group"], undefined);
      assert(!/\/(?:exec|portforward|watch)(?:\/|$)/.test(request.url.pathname));
      assert(["GET", "POST"].includes(request.method));
      if (request.url.pathname.endsWith("/pods")) assert.equal(request.url.searchParams.get("dryRun"), "All");
    }
    const reviews = fixture.requests.filter(request => request.url.pathname.endsWith("selfsubjectaccessreviews"));
    assert.equal(reviews.length, profile === "kata-in-cluster" ? 11 : 10);
    const pods = fixture.requests.filter(request => request.url.pathname.endsWith("/pods"));
    assert.equal(pods.length, profile === "kata-in-cluster" ? 99 : 72);
    assert.equal(pods[0].body.spec.runtimeClassName, profile === "kata-in-cluster" ? "kata-qemu-runtime-rs" : undefined);
    for (const hostProbe of pods.filter(request => request.url.pathname.includes("/namespaces/oci-js-host/"))) {
      assert.equal(hostProbe.body.spec.serviceAccountName, "oci-js-host");
      assert.equal(hostProbe.body.spec.automountServiceAccountToken, false);
      assert(!JSON.stringify(hostProbe.body).includes("oci-js-kata-oci-config"));
    }
    assert.equal(report.checks.find(check => check.id === "admission:image")?.statusCode, 422);
    assert.equal(report.checks.find(check => check.id === "admission:image")?.reason, "Invalid");
    assert.doesNotMatch(JSON.stringify(report), /secret-test-token|raw rejected pod|127\.0\.0\.1/);
  }
});

test("real SDK supports direct service-account credentials without impersonation", async t => {
  const fixture = await fakeApi(t, "in-cluster");
  fixture.state.identity = fixture.options.expectedIdentity!;
  const options = { ...fixture.options, impersonate: false };
  const report = await validateDeployment(options, createKubeconfigValidationApi(options));
  assert.equal(report.passed, true, JSON.stringify(report.checks.filter(check => check.outcome === "failed")));
  assert(fixture.requests.every(request => request.headers["impersonate-user"] === undefined));
});

test("deployment inspection requires the same explicit kubeconfig cluster", async t => {
  const fixture = await fakeApi(t);
  const source = JSON.parse(readFileSync(fixture.options.kubeconfigPath, "utf8"));
  source.clusters.push({ name: "other-cluster", cluster: { server: "https://other.invalid" } });
  source.contexts.push({ name: "other", context: { cluster: "other-cluster", user: "operator" } });
  writeFileSync(fixture.options.kubeconfigPath, JSON.stringify(source));
  assert.throws(() => createKubeconfigValidationApi({ ...fixture.options, inspectionContext: "other" }), /same kubeconfig cluster/);
  assert.equal(fixture.requests.length, 0);
});

test("node inspection follows pagination and fails on repeated cursors, excessive inventory or excessive pages", async t => {
  const fixture = await fakeApi(t, "kata-in-cluster");
  fixture.state.nodeResponse = index => index === 0
    ? { metadata: { continue: "next-page" }, items: [nodeFixtures()[0]] } : { items: [nodeFixtures()[1]] };
  const api = createKubeconfigValidationApi(fixture.options).inspection!;
  assert.equal((await api.listNodes(AbortSignal.timeout(2000))).length, 2);
  const requests = fixture.requests.filter(request => request.url.pathname === "/api/v1/nodes");
  assert.equal(requests[1].url.searchParams.get("continue"), "next-page");
  assert(requests.every(request => request.url.searchParams.get("limit") === "250" && request.headers["impersonate-user"] === undefined));
  for (const response of [
    () => ({ metadata: { continue: "repeat" }, items: [] }),
    () => ({ items: Array.from({ length: 1001 }, () => nodeFixtures()[0]) }),
    (index: number) => ({ metadata: { continue: `page-${index}` }, items: [] })
  ]) {
    fixture.state.nodeResponse = response;
    await assert.rejects(api.listNodes(AbortSignal.timeout(2000)), /validation bound/);
  }
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(api.listNodes(controller.signal), /aborted/);
});

test("SDK recognizes only structured matching Kubernetes rejection evidence", async t => {
  const fixture = await fakeApi(t, "in-cluster");
  const api = createKubeconfigValidationApi(fixture.options);
  const pod = buildExecutionPod(fixture.options.config, runtimePolicyFor(fixture.options.config), "validation", "correlation", Date.now() + 30_000);
  for (const [code, reason] of [[400, "BadRequest"], [403, "Forbidden"], [422, "Invalid"]] as const) {
    fixture.state.podResponse = { code, body: { apiVersion: "v1", kind: "Status", status: "Failure", code, reason } };
    assert.deepEqual(await api.dryRunCreatePod("execution", pod, new AbortController().signal), {
      outcome: "rejected", statusCode: code, reason
    });
  }
  for (const response of [
    { code: 403, body: {} }, { code: 422, body: "malformed" },
    { code: 403, body: { kind: "Status", status: "Failure", code: 403, reason: "Invalid" } },
    ...[401, 429, 500, 503].map(code => ({ code, body: { kind: "Status", status: "Failure", code, reason: "Forbidden" } }))
  ]) {
    fixture.state.podResponse = response;
    await assert.rejects(api.dryRunCreatePod("execution", pod, new AbortController().signal));
  }
});

test("denied impersonation cannot fall back to operator credentials", async t => {
  const fixture = await fakeApi(t, "in-cluster");
  fixture.state.identityDenied = true;
  const report = await validateDeployment(fixture.options, createKubeconfigValidationApi(fixture.options));
  assert.equal(report.passed, false);
  assert.equal(report.identity, null);
  assert.equal(fixture.requests.length, 1);
  assert.equal(report.checks[0].statusCode, 403);
});

test("SDK abort reaches a stalled HTTP request", { timeout: 3000 }, async t => {
  const fixture = await fakeApi(t, "in-cluster");
  const controller = new AbortController();
  let observedClose!: () => void;
  const closed = new Promise<void>(resolve => { observedClose = resolve; });
  fixture.state.stallNamespace = response => {
    response.once("close", observedClose);
    setTimeout(() => controller.abort(), 10);
  };
  const report = await validateDeployment(fixture.options, createKubeconfigValidationApi(fixture.options), controller.signal);
  assert.equal(report.passed, false);
  await closed;
  assert.equal(fixture.requests.length, 2);
});

test("validation does not accept incomplete rejection evidence from an adapter", async () => {
  const api = new ValidationApi("in-cluster");
  let count = 0;
  api.dryRunCreatePod = async () => ++count === 1
    ? { outcome: "accepted" } : { outcome: "rejected" } as AdmissionProbeResult;
  const report = await validateDeployment(parseValidationOptions(hostArgs, validInClusterEnvironment()), api);
  assert.equal(report.passed, false);
  assert.equal(report.checks.find(check => check.id === "admission:image")?.detail, "Inconclusive admission response");
});

test("namespace access and each lifecycle permission must pass before admission", async () => {
  const options = parseValidationOptions(hostArgs, validInClusterEnvironment());
  const namespace = new ValidationApi("in-cluster");
  namespace.readNamespace = async () => { throw new Error("raw namespace endpoint"); };
  assert.equal((await validateDeployment(options, namespace)).passed, false);
  assert.equal(namespace.pods.length, 0);
  for (let missing = 0; missing < 10; missing++) {
    const api = new ValidationApi("in-cluster");
    let count = 0;
    api.selfCan = async () => count++ !== missing;
    assert.equal((await validateDeployment(options, api)).passed, false);
    assert.equal(api.pods.length, 0);
  }
});

test("pre-abort, deadline expiry and late settlement cannot issue requests or mutate returned evidence", { timeout: 3000 }, async () => {
  const options = parseValidationOptions(hostArgs, validInClusterEnvironment());
  const preAborted = new AbortController();
  preAborted.abort();
  const unused = new ValidationApi("in-cluster");
  unused.identity = async () => { throw new Error("must not be called"); };
  assert.equal((await validateDeployment(options, unused, preAborted.signal)).passed, false);

  let late!: (value: { username: string; groups: string[] }) => void;
  let requestSignal!: AbortSignal;
  const api = new ValidationApi("in-cluster");
  api.identity = signal => {
    requestSignal = signal;
    return new Promise(resolve => { late = resolve; });
  };
  const report = await validateDeployment({ ...options, timeoutMs: 10 }, api);
  const snapshot = JSON.stringify(report);
  assert.equal(requestSignal.aborted, true);
  assert.equal(getEventListeners(requestSignal, "abort").length, 0);
  late({ username: options.expectedIdentity!, groups: hostGroups });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(JSON.stringify(report), snapshot);
  assert.equal(api.pods.length, 0);

  const rejection = new ValidationApi("in-cluster");
  let rejectLate!: (error: Error) => void;
  rejection.identity = () => new Promise((_resolve, reject) => { rejectLate = reject; });
  const rejected = await validateDeployment({ ...options, timeoutMs: 10 }, rejection);
  rejectLate(new Error("late rejection"));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(rejected.passed, false);
});

test("CLI removes signal listeners and emits sanitized JSON setup failures", async () => {
  const listeners = [process.listenerCount("SIGINT"), process.listenerCount("SIGTERM")];
  const output: string[] = [];
  assert.equal(await main(["--json"], {}, { write: value => output.push(value) }), 1);
  assert.deepEqual(JSON.parse(output[0]), { passed: false, error: "--kubeconfig and --context are required" });
  assert.deepEqual([process.listenerCount("SIGINT"), process.listenerCount("SIGTERM")], listeners);
});

test("fresh CLI processes report successful and failed JSON validation with matching exit codes", { timeout: 10_000 }, async t => {
  const fixture = await fakeApi(t, "in-cluster");
  const success = await runCli(fixture, ["--json"]);
  assert.equal(success.code, 0, success.stderr);
  assert.equal(JSON.parse(success.stdout).passed, true);
  assert.equal(success.stderr, "");
  fixture.state.acceptAll = true;
  const failure = await runCli(fixture, ["--json"]);
  assert.equal(failure.code, 1);
  assert.equal(JSON.parse(failure.stdout).passed, false);
});

test("fresh CLI deadline and SIGTERM bound a stalled validation", { timeout: 10_000 }, async t => {
  const fixture = await fakeApi(t, "in-cluster");
  fixture.state.stallNamespace = () => undefined;
  const deadline = await runCli(fixture, ["--json", "--timeout-seconds", "1"]);
  assert.equal(deadline.code, 1);
  assert.match(deadline.stdout, /cancelled or timed out/);
  let child!: ReturnType<typeof spawn>;
  fixture.state.stallNamespace = () => { child.kill("SIGTERM"); };
  const terminated = await runCli(fixture, ["--json"], value => { child = value; });
  assert.equal(terminated.code, 1);
  assert.match(terminated.stdout, /cancelled or timed out/);
});

test("CLI rejects non-cancellable exec credentials before launching the helper", { timeout: 10_000 }, async t => {
  const fixture = await fakeApi(t, "in-cluster");
  const kubeconfig = JSON.parse(readFileSync(fixture.options.kubeconfigPath, "utf8"));
  const marker = join(fixture.options.kubeconfigPath, "..", "helper-ran");
  kubeconfig.users[0].user = { exec: {
    apiVersion: "client.authentication.k8s.io/v1", command: process.execPath,
    args: ["-e", `require('node:fs').writeFileSync(${JSON.stringify(marker)}, 'ran'); setTimeout(() => console.log(JSON.stringify({apiVersion:'client.authentication.k8s.io/v1',kind:'ExecCredential',status:{token:'secret-test-token'}})), 200);`],
    interactiveMode: "Never"
  } };
  writeFileSync(fixture.options.kubeconfigPath, JSON.stringify(kubeconfig));
  const result = await runCli(fixture, ["--json", "--timeout-seconds", "1"]);
  assert.equal(result.code, 1);
  assert.match(JSON.parse(result.stdout).error, /exec.*auth-provider/);
  assert.throws(() => readFileSync(marker), { code: "ENOENT" });
  assert.equal(fixture.requests.length, 0);

  kubeconfig.users[0].user = { "auth-provider": { name: "oidc", config: { "id-token": "secret-test-token" } } };
  writeFileSync(fixture.options.kubeconfigPath, JSON.stringify(kubeconfig));
  assert.throws(() => createKubeconfigValidationApi(fixture.options), /exec.*auth-provider/);
});

test("validator import stays independent of the MCP provider, OCI host and native isolate", async t => {
  const hooks = registerHooks({ resolve(specifier, context, nextResolve) {
    const result = nextResolve(specifier, context);
    if (specifier === "isolated-vm" || /\/(?:server|oci-host|provider-factory|podman|kubernetes)\.ts$/.test(result.url)) {
      throw new Error(`Validator must not import ${specifier}`);
    }
    return result;
  } });
  t.after(() => hooks.deregister());
  const moduleUrl = new URL("../src/kubernetes-deployment-validation.ts", import.meta.url);
  moduleUrl.search = "?independence-check";
  await import(moduleUrl.href);
});

const hostGroups = ["system:authenticated", "system:serviceaccounts", "system:serviceaccounts:oci-js-host"];

class ValidationApi implements DeploymentValidationApi {
  readonly pods: KubernetesPod[] = [];
  readonly permissions: ResourceAttributes[] = [];
  runtimeReads = 0;
  acceptAll = false;
  negativeError = false;
  groups = hostGroups;
  fault?: "identity" | "permission" | "runtime" | "conforming" | "api";
  readonly profile: "local-development" | "in-cluster" | "kata-in-cluster";
  runtime = loadAllYaml(readFileSync("examples/kata-kubernetes/v1/05-runtime-class.yaml", "utf8"))[0] as import("@kubernetes/client-node").V1RuntimeClass;
  inspection: DeploymentInspectionApi = {
    identity: async () => ({ username: "deployment-reader", groups: [] }),
    readNamespace: async (name: string) => namespaceFixture(name, this.profile),
    readPolicy: async (name: string) => referenceAdmission(this.profile, "ValidatingAdmissionPolicy", name.includes("trusted-host-placement")),
    readBinding: async (name: string) => referenceAdmission(this.profile, "ValidatingAdmissionPolicyBinding", name.includes("trusted-host-placement")),
    listNodes: async () => nodeFixtures(),
    dryRunCreatePod: async (_namespace: string, pod: KubernetesPod): Promise<AdmissionProbeResult> =>
      deploymentProbeAccepted(pod, this.profile, true) ? { outcome: "accepted" }
        : { outcome: "rejected", statusCode: 422, reason: "Invalid" }
  };
  constructor(profile: "local-development" | "in-cluster" | "kata-in-cluster") {
    this.profile = profile;
  }
  async identity(_signal: AbortSignal) {
    if (this.fault === "api") throw Object.assign(new Error("secret cluster endpoint"), { code: 403 });
    return {
      username: this.fault === "identity" ? "operator" : "system:serviceaccount:oci-js-host:oci-js-host",
      groups: this.groups
    };
  }
  async readNamespace(name: string, _signal: AbortSignal): Promise<V1Namespace> { return namespaceFixture(name, this.profile); }
  async readRuntimeClass(_name: string, _signal: AbortSignal) {
    this.runtimeReads += 1;
    return this.fault === "runtime" ? { handler: "wrong-runtime" } : this.runtime;
  }
  async selfCan(permission: ResourceAttributes, _signal: AbortSignal): Promise<boolean> {
    this.permissions.push(permission);
    return this.fault !== "permission";
  }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod, _signal: AbortSignal): Promise<AdmissionProbeResult> {
    this.pods.push(pod);
    if (this.negativeError && this.pods.length === 2) throw Object.assign(new Error("secret cluster endpoint"), { code: 503 });
    return this.acceptAll || (this.fault !== "conforming" && deploymentProbeAccepted(pod, this.profile))
      ? { outcome: "accepted" } : { outcome: "rejected", statusCode: 422, reason: "Invalid" };
  }
}

function deploymentProbeAccepted(pod: KubernetesPod, profile: "local-development" | "in-cluster" | "kata-in-cluster", host = false): boolean {
  const spec = pod.spec!;
  if (host) return spec.nodeSelector?.["oci.oracle.com.node-restriction.kubernetes.io/workload-pool"] === "trusted-host"
    && !spec.runtimeClassName && !spec.nodeName && !spec.tolerations
    && (!spec.schedulerName || spec.schedulerName === "default-scheduler");
  if (!conformingPodAdmission(pod, profile)) return false;
  if (profile !== "kata-in-cluster") return true;
  const container = spec.containers[0]!;
  return !container.envFrom && !container.args && !container.workingDir && !container.stdin && !container.stdinOnce && !container.tty
    && Object.keys(pod.metadata!.labels!).length === 3 && Object.keys(pod.metadata!.annotations!).length === 5
    && pod.metadata!.annotations!["oci.oracle.com/trusted-host-namespace"] === "oci-js-host"
    && !!pod.metadata!.annotations!["oci.oracle.com/expires-at"] && !pod.metadata!.finalizers
    && !spec.nodeSelector && !spec.affinity && !spec.tolerations && !spec.nodeName && !spec.schedulerName
    && !spec.schedulingGates && !spec.topologySpreadConstraints && !spec.priorityClassName && !spec.preemptionPolicy;
}

function namespaceFixture(name: string, profile: string) {
  return { apiVersion: "v1", kind: "Namespace", metadata: { name, labels: {
    "kubernetes.io/metadata.name": name,
    "oci.oracle.com/kubernetes-profile": profile,
    "pod-security.kubernetes.io/enforce": "restricted"
  } } };
}

function nodeFixtures(): V1Node[] {
  return [{ metadata: { name: "execution-node", labels: {
    "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64",
    "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": "kata-execution",
    "oci.oracle.com.node-restriction.kubernetes.io/kata-profile": "kata-qemu-runtime-rs-v1"
  } }, spec: { taints: [{ key: "oci.oracle.com/workload-pool", value: "kata-execution", effect: "NoSchedule" }] },
  status: { conditions: [{ type: "Ready", status: "True" }], nodeInfo: {
    architecture: "amd64", operatingSystem: "linux", bootID: "example", containerRuntimeVersion: "example",
    kernelVersion: "example", kubeProxyVersion: "example", kubeletVersion: "example", machineID: "example",
    osImage: "example", systemUUID: "example"
  } } }, { metadata: { name: "trusted-node", labels: {
    "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": "trusted-host"
  } }, status: { conditions: [{ type: "Ready", status: "True" }] } }];
}

type RecordedRequest = { method: string; url: URL; headers: IncomingHttpHeaders; body: any };

async function fakeApi(t: TestContext, profile: "in-cluster" | "kata-in-cluster" = "in-cluster") {
  const requests: RecordedRequest[] = [];
  const state = {
    identity: "operator",
    identityDenied: false,
    acceptAll: false,
    podResponse: undefined as { code: number; body: unknown } | undefined,
    nodeRequests: 0,
    nodeResponse: undefined as ((index: number) => { items: V1Node[]; metadata?: { continue: string } }) | undefined,
    stallNamespace: undefined as ((response: import("node:http").ServerResponse) => void) | undefined
  };
  const server = createServer(async (request, response) => {
    let source = "";
    for await (const chunk of request) source += String(chunk);
    const body = source ? JSON.parse(source) : undefined;
    const url = new URL(request.url!, "http://localhost");
    requests.push({ method: request.method!, url, headers: request.headers, body });
    const send = (value: unknown, code = 200) => {
      response.writeHead(code, { "content-type": "application/json" });
      response.end(JSON.stringify(value));
    };
    if (url.pathname.endsWith("selfsubjectreviews")) {
      return state.identityDenied
        ? send({ kind: "Status", status: "Failure", code: 403, reason: "Forbidden" }, 403)
        : send({ apiVersion: "authentication.k8s.io/v1", kind: "SelfSubjectReview", status: {
          userInfo: { username: request.headers["impersonate-user"] ?? state.identity, groups: hostGroups }
        } });
    }
    if (url.pathname.endsWith("selfsubjectaccessreviews")) {
      return send({ apiVersion: "authorization.k8s.io/v1", kind: "SelfSubjectAccessReview", status: { allowed: true } });
    }
    if (url.pathname.includes("/runtimeclasses/")) return send(loadAllYaml(readFileSync("examples/kata-kubernetes/v1/05-runtime-class.yaml", "utf8"))[0]);
    if (url.pathname.includes("/validatingadmissionpolic")) {
      return send(referenceAdmission(profile, url.pathname.includes("validatingadmissionpolicybindings")
        ? "ValidatingAdmissionPolicyBinding" : "ValidatingAdmissionPolicy", url.pathname.includes("trusted-host-placement")));
    }
    if (url.pathname === "/api/v1/nodes") return send({ apiVersion: "v1", kind: "NodeList",
      ...(state.nodeResponse?.(state.nodeRequests++) ?? { items: nodeFixtures() }) });
    if (url.pathname.endsWith("/pods")) {
      if (state.podResponse) return send(state.podResponse.body, state.podResponse.code);
      // The shared fixture compares mount JSON; normalize the SDK's property ordering.
      const pod = structuredClone(body);
      pod.spec.containers[0].volumeMounts = pod.spec.containers[0].volumeMounts?.map(
        ({ name, mountPath, readOnly, ...rest }: Record<string, unknown>) => ({ name, mountPath, readOnly, ...rest })
      );
      return state.acceptAll || deploymentProbeAccepted(pod, profile, url.pathname.includes("/namespaces/oci-js-host/")) ? send(body, 201) : send({
        apiVersion: "v1", kind: "Status", status: "Failure", code: 422, reason: "Invalid", message: "raw rejected pod"
      }, 422);
    }
    if (state.stallNamespace) return state.stallNamespace(response);
    send(namespaceFixture(decodeURIComponent(url.pathname.split("/").at(-1)!), profile));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(async () => { server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve())); });
  const directory = mkdtempSync(join(tmpdir(), "oci-js-validation-sdk-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const path = join(directory, "config");
  writeFileSync(path, JSON.stringify({
    apiVersion: "v1", kind: "Config",
    // The SDK requires this flag for the loopback HTTP fixture; no live TLS is bypassed.
    clusters: [{ name: "cluster", cluster: {
      server: `http://127.0.0.1:${(server.address() as import("node:net").AddressInfo).port}`,
      "insecure-skip-tls-verify": true
    } }],
    users: [{ name: "operator", user: { token: "secret-test-token" } }],
    contexts: [{ name: "target", context: { cluster: "cluster", user: "operator" } }],
    "current-context": "not-selected"
  }));
  const cliArgs = ["--kubeconfig", path, "--context", "target", "--host-service-account", "oci-js-host", "--impersonate", "--inspection-context", "target"];
  const environment = profile === "kata-in-cluster" ? validKataEnvironment() : validInClusterEnvironment();
  return { requests, state, options: parseValidationOptions(cliArgs, environment), cliArgs, environment };
}

async function runCli(fixture: Awaited<ReturnType<typeof fakeApi>>, extraArgs: string[],
  observe?: (child: ReturnType<typeof spawn>) => void) {
  const child = spawn(process.execPath, ["--no-node-snapshot", "--experimental-strip-types",
    fileURLToPath(new URL("../src/kubernetes-deployment-validation.ts", import.meta.url)),
    ...fixture.cliArgs, ...extraArgs], {
    env: { ...fixture.environment, NODE_V8_COVERAGE: process.env.NODE_V8_COVERAGE },
    stdio: ["ignore", "pipe", "pipe"]
  });
  observe?.(child);
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", chunk => { stdout += String(chunk); });
  child.stderr.on("data", chunk => { stderr += String(chunk); });
  const [code] = await once(child, "close");
  return { code, stdout, stderr };
}
