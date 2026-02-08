const state = {
  apiKey: "",
  apiHost: "https://us.i.posthog.com",
  defaults: "",
  disabled: false,
  distinctId: "",
  anonymousId: "",
  identifiedProps: {},
  pageleaveBound: false,
};

function normalizeApiHost(value) {
  return String(value || "").replace(/\/+$/, "");
}

function getFetchFn() {
  if (
    typeof globalThis !== "undefined" &&
    typeof globalThis.fetch === "function"
  ) {
    return globalThis.fetch.bind(globalThis);
  }

  return null;
}

function getAnonymousId() {
  if (!state.anonymousId) {
    const randomPart = Math.random().toString(36).slice(2);
    state.anonymousId = `anon-${Date.now()}-${randomPart}`;
  }

  return state.anonymousId;
}

function getDistinctId() {
  return state.distinctId || getAnonymousId();
}

function buildPayload(event, properties = {}) {
  return {
    api_key: state.apiKey,
    event,
    properties: {
      token: state.apiKey,
      distinct_id: getDistinctId(),
      ...state.identifiedProps,
      ...properties,
      $lib: "posthog-js-local",
      $lib_version: "0.0.1-local",
    },
    timestamp: new Date().toISOString(),
  };
}

function sendEvent(event, properties = {}, options = {}) {
  const fetchFn = getFetchFn();
  if (state.disabled || !state.apiKey || !fetchFn) {
    return;
  }

  const endpoint = `${normalizeApiHost(state.apiHost)}/i/v0/e/`;
  const payload = JSON.stringify(buildPayload(event, properties));

  if (
    options.useBeacon &&
    typeof globalThis !== "undefined" &&
    typeof globalThis.navigator !== "undefined" &&
    typeof globalThis.navigator.sendBeacon === "function" &&
    typeof globalThis.Blob === "function"
  ) {
    try {
      const blob = new globalThis.Blob([payload], { type: "application/json" });
      globalThis.navigator.sendBeacon(endpoint, blob);
      return;
    } catch {
      // Fallback to fetch below.
    }
  }

  fetchFn(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    mode: "cors",
    credentials: "omit",
    keepalive: Boolean(options.keepalive),
    body: payload,
  }).catch(() => {
    // Tracking failures should never break app UX.
  });
}

const posthog = {
  init(apiKey, options = {}) {
    state.apiKey = String(apiKey || "");
    state.apiHost = normalizeApiHost(options.api_host || state.apiHost);
    state.defaults = String(options.defaults || "");
    state.disabled = false;

    if (
      options.capture_pageleave &&
      typeof globalThis !== "undefined" &&
      typeof globalThis.addEventListener === "function" &&
      !state.pageleaveBound
    ) {
      globalThis.addEventListener("pagehide", () => {
        sendEvent("$pageleave", { defaults: state.defaults }, { useBeacon: true });
      });
      state.pageleaveBound = true;
    }
  },

  capture(event, properties = {}) {
    sendEvent(event, properties, { keepalive: true });
  },

  identify(distinctId, properties = {}) {
    const previousDistinctId = getDistinctId();
    if (distinctId) {
      state.distinctId = String(distinctId);
    }

    if (properties && typeof properties === "object") {
      state.identifiedProps = { ...state.identifiedProps, ...properties };
    }

    const identifyProps = {
      distinct_id: getDistinctId(),
      $set: properties,
    };

    if (previousDistinctId && previousDistinctId !== getDistinctId()) {
      identifyProps.$anon_distinct_id = previousDistinctId;
    }

    sendEvent("$identify", identifyProps, { keepalive: true });
  },

  reset() {
    state.distinctId = "";
    state.anonymousId = "";
    state.identifiedProps = {};
  },

  opt_out_capturing() {
    state.disabled = true;
  },

  opt_in_capturing() {
    state.disabled = false;
  },
};

export default posthog;
