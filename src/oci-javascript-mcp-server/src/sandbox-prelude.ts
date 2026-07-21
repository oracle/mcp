/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

export const SANDBOX_BOOTSTRAP = `
"use strict";

const __hostConsoleLog = $0;
const __hostConsoleError = $1;
const __hostRpc = $2;
const __sandboxStdin = $3;
const __ociReflectionManifest = $4 || { services: {} };
const __ociWireTypeKey = "__oci_wire_type";
const __ociBase64Alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
const __ociMaxDepth = 80;
const __arrayFrom = Array.from;
const __arrayIsArray = Array.isArray;
const __bigInt = BigInt;
const __date = Date;
const __error = Error;
const __eval = eval;
const __function = Function;
const __map = Map;
const __jsonStringify = JSON.stringify;
const __number = Number;
const __numberIsFinite = Number.isFinite;
const __numberIsNaN = Number.isNaN;
const __objectAssign = Object.assign;
const __objectDefineProperty = Object.defineProperty;
const __objectEntries = Object.entries;
const __objectFreeze = Object.freeze;
const __objectGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
const __objectKeys = Object.keys;
const __promiseAllSettled = Promise.allSettled.bind(Promise);
const __proxy = Proxy;
const __reflectOwnKeys = Reflect.ownKeys;
const __set = Set;
const __string = String;
const __uint8Array = Uint8Array;
const __weakSet = WeakSet;
const __ociRpcPending = new __set();
const __serviceProxyCache = new __map();
const __clientProxyCache = new __map();
const __ociRegionIdPattern = /^[a-z][a-z0-9-]*-[a-z0-9-]+-[0-9]+$/;

function __ociWireValue(typeName, fields) {
  return __objectAssign({ [__ociWireTypeKey]: typeName }, fields);
}

function __ociBase64Encode(bytes) {
  let result = "";
  for (let index = 0; index < bytes.length; index += 3) {
    const first = bytes[index];
    const second = index + 1 < bytes.length ? bytes[index + 1] : 0;
    const third = index + 2 < bytes.length ? bytes[index + 2] : 0;
    const triple = (first << 16) | (second << 8) | third;
    result += __ociBase64Alphabet[(triple >> 18) & 63];
    result += __ociBase64Alphabet[(triple >> 12) & 63];
    result += index + 1 < bytes.length ? __ociBase64Alphabet[(triple >> 6) & 63] : "=";
    result += index + 2 < bytes.length ? __ociBase64Alphabet[triple & 63] : "=";
  }
  return result;
}

function __ociBase64Decode(value) {
  const clean = __string(value || "").replace(/[^A-Za-z0-9+/=]/g, "");
  const bytes = [];
  for (let index = 0; index < clean.length; index += 4) {
    const first = __ociBase64Alphabet.indexOf(clean[index]);
    const second = __ociBase64Alphabet.indexOf(clean[index + 1]);
    const third = clean[index + 2] === "=" ? -1 : __ociBase64Alphabet.indexOf(clean[index + 2]);
    const fourth = clean[index + 3] === "=" ? -1 : __ociBase64Alphabet.indexOf(clean[index + 3]);
    if (first < 0 || second < 0) {
      break;
    }
    const triple = (first << 18) | (second << 12) | ((third < 0 ? 0 : third) << 6) | (fourth < 0 ? 0 : fourth);
    bytes.push((triple >> 16) & 255);
    if (third >= 0) {
      bytes.push((triple >> 8) & 255);
    }
    if (fourth >= 0) {
      bytes.push(triple & 255);
    }
  }
  return __uint8Array.from(bytes);
}

function __ociToWire(value, seen = new __weakSet(), depth = 0) {
  if (depth > __ociMaxDepth) {
    return __ociWireValue("repr", { value: "[MaxDepth]" });
  }
  if (value === null || value === undefined) {
    return null;
  }
  const typeName = typeof value;
  if (typeName === "string" || typeName === "boolean" || typeName === "number") {
    if (typeName === "number" && !__numberIsFinite(value)) {
      if (__numberIsNaN(value)) {
        return __ociWireValue("float", { value: "nan" });
      }
      return __ociWireValue("float", { value: value > 0 ? "inf" : "-inf" });
    }
    return value;
  }
  if (typeName === "bigint") {
    return __ociWireValue("bigint", { value: value.toString() });
  }
  if (typeName === "function" || typeName === "symbol") {
    return __ociWireValue("repr", { value: __string(value) });
  }
  if (value instanceof __date) {
    return __ociWireValue("datetime", { value: value.toISOString() });
  }
  if (value instanceof __uint8Array) {
    return __ociWireValue("bytes", { encoding: "base64", value: __ociBase64Encode(value) });
  }
  if (typeName === "object") {
    if (seen.has(value)) {
      return __ociWireValue("repr", { value: "[Circular]" });
    }
    seen.add(value);
    try {
      if (__arrayIsArray(value)) {
        return value.map(item => __ociToWire(item, seen, depth + 1));
      }
      if (value instanceof __map) {
        return __ociWireValue("map", {
          items: __arrayFrom(value.entries()).map(([key, item]) => [
            __ociToWire(key, seen, depth + 1),
            __ociToWire(item, seen, depth + 1)
          ])
        });
      }
      if (value instanceof __set) {
        return __ociWireValue("set", {
          items: __arrayFrom(value.values()).map(item => __ociToWire(item, seen, depth + 1))
        });
      }
      const result = {};
      for (const [key, item] of __objectEntries(value)) {
        if (item !== undefined) {
          result[key] = __ociToWire(item, seen, depth + 1);
        }
      }
      return result;
    } finally {
      seen.delete(value);
    }
  }
  return __ociWireValue("repr", { value: __string(value) });
}

function __ociFloatFromWire(value) {
  if (value === "nan") {
    return __number.NaN;
  }
  if (value === "inf") {
    return __number.POSITIVE_INFINITY;
  }
  if (value === "-inf") {
    return __number.NEGATIVE_INFINITY;
  }
  return __number(value);
}

function __ociFromWire(value) {
  if (__arrayIsArray(value)) {
    return value.map(item => __ociFromWire(item));
  }
  if (!value || typeof value !== "object") {
    return value;
  }

  const wireType = value[__ociWireTypeKey];
  if (wireType === "datetime" || wireType === "date" || wireType === "time") {
    return new __date(value.value);
  }
  if (wireType === "bigint") {
    return __bigInt(value.value);
  }
  if (wireType === "bytes") {
    return __ociBase64Decode(value.value);
  }
  if (wireType === "float") {
    return __ociFloatFromWire(value.value);
  }
  if (wireType === "map") {
    return new __map((value.items || []).map(item => [
      __ociFromWire(item[0]),
      __ociFromWire(item[1])
    ]));
  }
  if (wireType === "set") {
    return new __set((value.items || []).map(item => __ociFromWire(item)));
  }
  if (wireType === "repr") {
    return value.value;
  }
  if (__ociWireTypeKey in value) {
    throw new __error("Unknown OCI wire type '" + __string(wireType) + "'");
  }

  const result = {};
  for (const [key, item] of __objectEntries(value)) {
    result[key] = __ociFromWire(item);
  }
  return result;
}

function __ociFormat(value) {
  const plain = __ociToWire(value);
  if (typeof plain === "string") {
    return plain;
  }
  if (plain === null) {
    return __string(value);
  }
  try {
    return __jsonStringify(plain, null, 2);
  } catch (_error) {
    return __string(value);
  }
}

const __ociConsole = __objectFreeze({
  log: (...args) => {
    __hostConsoleLog.applySync(undefined, [args.map(__ociFormat).join(" ") + "\\n"], {
      arguments: { copy: true },
      result: { copy: true }
    });
  },
  error: (...args) => {
    __hostConsoleError.applySync(undefined, [args.map(__ociFormat).join(" ") + "\\n"], {
      arguments: { copy: true },
      result: { copy: true }
    });
  }
});

__objectDefineProperty(globalThis, "console", {
  value: __ociConsole,
  writable: false,
  enumerable: true,
  configurable: false
});

__objectDefineProperty(globalThis, "stdin", {
  value: __sandboxStdin,
  writable: false,
  enumerable: true,
  configurable: false
});

async function __ociRpc(operation, payload) {
  const request = __ociToWire({
    binding: "oracle",
    namespace: "oci",
    operation,
    payload
  });
  const promise = __hostRpc.apply(undefined, [request], {
    arguments: { copy: true },
    result: { promise: true, copy: true }
  });
  __ociRpcPending.add(promise);
  try {
    const envelope = await promise;
    if (!envelope || envelope.ok !== true) {
      throw __ociErrorFromEnvelope(envelope && envelope.error);
    }
    return __ociFromWire(envelope.value);
  } finally {
    __ociRpcPending.delete(promise);
  }
}

function __ociErrorFromEnvelope(error) {
  if (!error || typeof error !== "object") {
    return new __error(__string(error || "OCI call failed"));
  }

  const message = typeof error.message === "string" && error.message
    ? error.message
    : "OCI call failed";
  const thrown = new __error(message);
  for (const [key, value] of __objectEntries(error)) {
    if (key !== "message") {
      try {
        thrown[key] = value;
      } catch (_error) {
        // Best effort: the message still carries the useful summary.
      }
    }
  }
  return thrown;
}

function __ociExecutionScript(code) {
  return [
    "\\"use strict\\";",
    "(async () => {",
    "globalThis._ = await (async () => {",
    __ociInferFinalReturn(code),
    "})();",
    "})()"
  ].join("\\n");
}

function __ociInferFinalReturn(code) {
  const trimmed = code.replace(/[\\s;]*$/g, "");
  for (const start of __ociFinalExpressionStarts(trimmed)) {
    const expression = trimmed.slice(start).trim();
    if (expression && __ociIsExpression(expression)) {
      return trimmed.slice(0, start) + "\\nreturn (" + expression + ");";
    }
  }
  return code;
}

function __ociFinalExpressionStarts(code) {
  const starts = [0];
  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;

  for (let index = 0; index < code.length; index += 1) {
    const char = code[index];
    const next = code[index + 1];

    if (lineComment) {
      if (char === "\\n") {
        lineComment = false;
        starts.push(index + 1);
      }
      continue;
    }
    if (blockComment) {
      if (char === "*" && next === "/") {
        blockComment = false;
        index += 1;
      }
      continue;
    }
    if (quote) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\\\") {
        escaped = true;
      } else if (char === quote) {
        quote = null;
      }
      continue;
    }
    if (char === "/" && next === "/") {
      lineComment = true;
      index += 1;
      continue;
    }
    if (char === "/" && next === "*") {
      blockComment = true;
      index += 1;
      continue;
    }
    if (char === "\\"" || char === "'" || char === "\`") {
      quote = char;
      continue;
    }
    if (char === "(" || char === "[" || char === "{") {
      depth += 1;
    } else if (char === ")" || char === "]" || char === "}") {
      depth = Math.max(0, depth - 1);
    } else if (depth === 0 && (char === ";" || char === "\\n")) {
      starts.push(index + 1);
    }
  }

  return starts.reverse();
}

function __ociIsExpression(source) {
  try {
    new __function("return (async () => (" + source + "));");
    return true;
  } catch (_error) {
    return false;
  }
}

function __ociValidateName(value, label) {
  if (typeof value !== "string" || !/^[A-Za-z][A-Za-z0-9_]*$/.test(value)) {
    throw new __error("Invalid OCI " + label + " " + __string(value));
  }
}

function __ociIsObjectProtocolKey(value) {
  return value === "then" || value === "catch" || value === "finally" || value === "toJSON";
}

function __ociIsBindingReservedKey(value) {
  return __ociIsObjectProtocolKey(value) || value === "paginate";
}

function __ociManifestServices() {
  return (__ociReflectionManifest && __ociReflectionManifest.services) || {};
}

function __ociManifestClients(service) {
  const serviceEntry = __ociManifestServices()[service];
  return (serviceEntry && serviceEntry.clients) || {};
}

function __ociManifestOperations(service, client) {
  const clientEntry = __ociManifestClients(service)[client];
  return (clientEntry && clientEntry.operations) || [];
}

function __ociMergedKeys(targetKeys, manifestKeys) {
  const result = [];
  const seen = new __set();
  for (const key of [...targetKeys, ...manifestKeys]) {
    if ((typeof key === "string" || typeof key === "symbol") && !seen.has(key)) {
      seen.add(key);
      result.push(key);
    }
  }
  return result;
}

function __ociDescriptor(value) {
  return {
    value,
    writable: false,
    enumerable: true,
    configurable: true
  };
}

function __ociNormalizeClientOptions(options) {
  if (options === undefined || options === null) {
    return {};
  }
  if (typeof options !== "object" || __arrayIsArray(options)) {
    throw new __error("OCI client options must be a plain object");
  }
  const result = {};
  for (const key of __objectKeys(options)) {
    if (key !== "region") {
      throw new __error(
        "Unsupported OCI client option '" + key
        + "'. Client options only support region; pass tenancyId, compartmentId, "
        + "and other OCI values in operation request objects."
      );
    }
  }
  if (options.region !== undefined) {
    if (typeof options.region !== "string" || !__ociRegionIdPattern.test(options.region)) {
      throw new __error("Invalid OCI client option region '" + __string(options.region) + "'");
    }
    result.region = options.region;
  }
  return result;
}

function __ociClient(service, client, options) {
  __ociValidateName(service, "service");
  __ociValidateName(client, "client");
  const normalizedOptions = __ociNormalizeClientOptions(options);
  const cacheKey = service + "." + client + ".instance." + (normalizedOptions.region || "");
  if (__clientProxyCache.has(cacheKey)) {
    return __clientProxyCache.get(cacheKey);
  }
  const target = {};
  const proxy = new __proxy(target, {
    get(_target, operation) {
      if (typeof operation !== "string" || operation.startsWith("_") || __ociIsObjectProtocolKey(operation)) {
        return undefined;
      }
      __ociValidateName(operation, "operation");
      return async request => __ociRpc("invoke", {
        service,
        client: __objectKeys(normalizedOptions).length > 0
          ? { name: client, options: normalizedOptions }
          : { name: client },
        operation,
        request: request ?? {}
      });
    },
    has(_target, operation) {
      return typeof operation === "string"
        && __ociManifestOperations(service, client).includes(operation);
    },
    ownKeys() {
      return __ociMergedKeys(__reflectOwnKeys(target), __ociManifestOperations(service, client));
    },
    getOwnPropertyDescriptor(_target, operation) {
      const descriptor = __objectGetOwnPropertyDescriptor(target, operation);
      if (descriptor) {
        return descriptor;
      }
      if (typeof operation === "string"
        && __ociManifestOperations(service, client).includes(operation)) {
        return __ociDescriptor(proxy[operation]);
      }
      return undefined;
    },
    set() {
      return false;
    },
    defineProperty() {
      return false;
    },
    deleteProperty() {
      return false;
    },
    setPrototypeOf() {
      return false;
    }
  });
  __clientProxyCache.set(cacheKey, proxy);
  return proxy;
}

function __ociClientFactory(service, client) {
  const target = function OciClient(options) {
    return __ociClient(service, client, options);
  };
  const cacheKey = service + "." + client + ".factory";
  if (__clientProxyCache.has(cacheKey)) {
    return __clientProxyCache.get(cacheKey);
  }
  const proxy = new __proxy(target, {
    apply(_target, _thisArg, args) {
      return __ociClient(service, client, args[0]);
    },
    construct(_target, args) {
      return __ociClient(service, client, args[0]);
    },
    get(_target, operation) {
      if (__ociIsObjectProtocolKey(operation)) {
        return undefined;
      }
      const descriptor = __objectGetOwnPropertyDescriptor(target, operation);
      if (descriptor && "value" in descriptor) {
        return descriptor.value;
      }
      return __ociClient(service, client)[operation];
    },
    has(_target, operation) {
      return operation in target
        || (typeof operation === "string"
          && __ociManifestOperations(service, client).includes(operation));
    },
    ownKeys() {
      return __ociMergedKeys(__reflectOwnKeys(target), __ociManifestOperations(service, client));
    },
    getOwnPropertyDescriptor(_target, operation) {
      const descriptor = __objectGetOwnPropertyDescriptor(target, operation);
      if (descriptor) {
        return descriptor;
      }
      if (typeof operation === "string"
        && __ociManifestOperations(service, client).includes(operation)) {
        return __ociDescriptor(__ociClient(service, client)[operation]);
      }
      return undefined;
    },
    set() {
      return false;
    },
    defineProperty() {
      return false;
    },
    deleteProperty() {
      return false;
    },
    setPrototypeOf() {
      return false;
    }
  });
  __clientProxyCache.set(cacheKey, proxy);
  return proxy;
}

function __ociService(service) {
  __ociValidateName(service, "service");
  if (__serviceProxyCache.has(service)) {
    return __serviceProxyCache.get(service);
  }
  const target = {};
  const proxy = new __proxy(target, {
    get(_target, client) {
      if (typeof client !== "string" || client.startsWith("_") || __ociIsObjectProtocolKey(client)) {
        return undefined;
      }
      __ociValidateName(client, "client");
      return __ociClientFactory(service, client);
    },
    has(_target, client) {
      return typeof client === "string"
        && client in __ociManifestClients(service);
    },
    ownKeys() {
      return __ociMergedKeys(__reflectOwnKeys(target), __objectKeys(__ociManifestClients(service)));
    },
    getOwnPropertyDescriptor(_target, client) {
      const descriptor = __objectGetOwnPropertyDescriptor(target, client);
      if (descriptor) {
        return descriptor;
      }
      if (typeof client === "string" && client in __ociManifestClients(service)) {
        return __ociDescriptor(__ociClientFactory(service, client));
      }
      return undefined;
    },
    set() {
      return false;
    },
    defineProperty() {
      return false;
    },
    deleteProperty() {
      return false;
    },
    setPrototypeOf() {
      return false;
    }
  });
  __serviceProxyCache.set(service, proxy);
  return proxy;
}

const __ociBindingTarget = {
  client: (service, client, options) => __ociClient(service, client, options),
  config: async () => __ociRpc("config", {})
};

const __ociBinding = new __proxy(__ociBindingTarget, {
  get(target, service) {
    if (service in target) {
      return target[service];
    }
    if (typeof service !== "string" || service.startsWith("_") || __ociIsBindingReservedKey(service)) {
      return undefined;
    }
    return __ociService(service);
  },
  has(target, service) {
    return service in target
      || (typeof service === "string"
        && !__ociIsBindingReservedKey(service)
        && service in __ociManifestServices());
  },
  ownKeys() {
    return __ociMergedKeys(
      __reflectOwnKeys(__ociBindingTarget),
      __objectKeys(__ociManifestServices()).filter(service => !__ociIsBindingReservedKey(service))
    );
  },
  getOwnPropertyDescriptor(target, service) {
    const descriptor = __objectGetOwnPropertyDescriptor(target, service);
    if (descriptor) {
      return descriptor;
    }
    if (typeof service === "string"
      && !__ociIsBindingReservedKey(service)
      && service in __ociManifestServices()) {
      return __ociDescriptor(__ociService(service));
    }
    return undefined;
  },
  set() {
    return false;
  },
  defineProperty() {
    return false;
  },
  deleteProperty() {
    return false;
  },
  setPrototypeOf() {
    return false;
  }
});

__objectDefineProperty(globalThis, "oci", {
  value: __ociBinding,
  writable: false,
  enumerable: true,
  configurable: false
});

return __objectFreeze({
  drain: async function __ociDrainPending() {
    while (__ociRpcPending.size > 0) {
      await __promiseAllSettled(__arrayFrom(__ociRpcPending));
    }
  },
  encodeLastResult: function __ociEncodeLastResult() {
    return __ociToWire(globalThis._);
  },
  run: async function __ociRun(code) {
    await __eval(__ociExecutionScript(code));
  }
});
`;
