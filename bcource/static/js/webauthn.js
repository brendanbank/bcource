/**
 * WebAuthn JavaScript handler
 * Handles registration and authentication using the Web Authentication API
 */

/**
 * Handle WebAuthn registration (creating a new credential)
 * @param {string} credentialOptionsJSON - JSON string containing credential creation options
 * @returns {Promise<{credential: string}|{error_msg: string}>}
 */
async function handleRegister(credentialOptionsJSON) {
  try {
    const credentialOptions = JSON.parse(credentialOptionsJSON);

    // Convert base64url strings to ArrayBuffers
    credentialOptions.user.id = base64urlToBuffer(credentialOptions.user.id);
    credentialOptions.challenge = base64urlToBuffer(credentialOptions.challenge);

    if (credentialOptions.excludeCredentials) {
      for (let cred of credentialOptions.excludeCredentials) {
        cred.id = base64urlToBuffer(cred.id);
      }
    }

    // Call the browser's WebAuthn API
    const credential = await navigator.credentials.create({
      publicKey: credentialOptions
    });

    // Convert the credential response to a format the server can process
    const credentialJSON = {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
        attestationObject: bufferToBase64url(credential.response.attestationObject)
      }
    };

    // Include transports if available (helps with future authentication)
    if (credential.response.getTransports) {
      credentialJSON.transports = credential.response.getTransports();
    }

    return { credential: JSON.stringify(credentialJSON) };
  } catch (err) {
    console.error('WebAuthn registration error:', err);
    return { error_msg: err.message || 'Registration failed. Please try again.' };
  }
}

/**
 * Handle WebAuthn authentication (signing in with existing credential)
 * @param {string} credentialOptionsJSON - JSON string containing credential request options
 * @returns {Promise<{credential: string}|{error_msg: string}>}
 */
async function handleSignin(credentialOptionsJSON) {
  try {
    const credentialOptions = JSON.parse(credentialOptionsJSON);

    // Convert base64url strings to ArrayBuffers
    credentialOptions.challenge = base64urlToBuffer(credentialOptions.challenge);

    if (credentialOptions.allowCredentials) {
      for (let cred of credentialOptions.allowCredentials) {
        cred.id = base64urlToBuffer(cred.id);
      }
    }

    // Call the browser's WebAuthn API
    const credential = await navigator.credentials.get({
      publicKey: credentialOptions
    });

    // Convert the credential response to a format the server can process
    const credentialJSON = {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
        authenticatorData: bufferToBase64url(credential.response.authenticatorData),
        signature: bufferToBase64url(credential.response.signature)
      }
    };

    // Include userHandle if present (for resident/discoverable credentials)
    if (credential.response.userHandle) {
      credentialJSON.response.userHandle = bufferToBase64url(credential.response.userHandle);
    }

    return { credential: JSON.stringify(credentialJSON) };
  } catch (err) {
    console.error('WebAuthn authentication error:', err);
    return { error_msg: err.message || 'Authentication failed. Please try again.' };
  }
}

/**
 * Check if WebAuthn is supported in the current browser
 * @returns {boolean}
 */
function isWebAuthnSupported() {
  return window.PublicKeyCredential !== undefined &&
         navigator.credentials !== undefined;
}

/**
 * Check if platform authenticator is available (biometric sensors)
 * @returns {Promise<boolean>}
 */
async function isPlatformAuthenticatorAvailable() {
  if (!isWebAuthnSupported()) {
    return false;
  }

  try {
    return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
  } catch (err) {
    console.error('Error checking platform authenticator:', err);
    return false;
  }
}
