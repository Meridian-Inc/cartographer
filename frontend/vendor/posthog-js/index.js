const state = {
  apiKey: "",
  apiHost: "https://us.i.posthog.com",
  defaults: "",
  disabled: false,
  distinctId: "",
  identifiedProps: {},
  pageleaveBound: false,
};

function getAnonymousId() {
  if (state.distinctId) {
    return state.distinctId;
  }

  const randomPart = Math.random().toString(36).slice(2);
  state.distinctId = `anon-${Date.now()}-${randomPart}`;
  return state.distinctId;
}

function enqueue(event, properties = {}) {
  const fetchFn =
    typeof globalThis !== "undefined" &&
    typeof globalThis.fetch === "function"
      ? globalThis.fetch.bind(globalThis)
      : null;

  if (state.disabled || !state.apiKey || !fetchFn) {
    return;
  }

  const payload = {
    api_key: state.apiKey,
    event,
    distinct_id: getAnonymousId(),
    properties: {
      ...state.identifiedProps,
      ...properties,
      $lib: "posthog-js-local",
      $lib_version: "0.0.0-local",
    },
    timestamp: new Date().toISOString(),
  };

  fetchFn(`${state.apiHost}/capture/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    keepalive: true,
    body: JSON.stringify(payload),
  }).catch(() => {
    // Tracking failures should never break app UX.
  });
}

const posthog = {
  init(apiKey, options = {}) {
    state.apiKey = apiKey || "";
    state.apiHost = options.api_host || state.apiHost;
    state.defaults = options.defaults || "";
    state.disabled = false;

    if (
      options.capture_pageleave &&
      typeof globalThis !== "undefined" &&
      typeof globalThis.addEventListener === "function" &&
      !state.pageleaveBound
    ) {
      globalThis.addEventListener("beforeunload", () => {
        enqueue("$pageleave", { defaults: state.defaults });
      });
      state.pageleaveBound = true;
    }
  },

  capture(event, properties = {}) {
    enqueue(event, properties);
  },

  identify(distinctId, properties = {}) {
    if (distinctId) {
      state.distinctId = String(distinctId);
    }

    if (properties && typeof properties === "object") {
      state.identifiedProps = { ...state.identifiedProps, ...properties };
    }

    enqueue("$identify", {
      distinct_id: state.distinctId,
      $set: properties,
    });
  },

  reset() {
    state.distinctId = "";
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
