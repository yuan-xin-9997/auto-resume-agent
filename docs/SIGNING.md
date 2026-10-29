# Optional signing and notarization

Default builds are **unsigned and not notarized**. No certificate, private key,
or Apple notarization credential is included in this repository, and the build
script does not sign automatically. The commands below are an optional
maintainer setup; do not commit secrets or run them without an approved
certificate.

## Windows (optional)

Provide your own code-signing certificate in the normal Windows certificate
store, then sign the built executables before packaging. Example placeholders:

```powershell
signtool sign /sha1 <CERT_THUMBPRINT> /fd SHA256 /tr <TIMESTAMP_URL> /td SHA256 `
  dist\auto-resume-agent\auto-resume-agent.exe
signtool sign /sha1 <CERT_THUMBPRINT> /fd SHA256 /tr <TIMESTAMP_URL> /td SHA256 `
  dist\AutoResumeAgent\AutoResumeAgent.exe
```

Verify with `signtool verify /pa /v <file>`. A signed installer or archive is
still not a guarantee of SmartScreen reputation.

## macOS (optional)

Use a Developer ID Application identity and the `notarytool` keychain profile
configured on the build machine. Example placeholders:

```sh
codesign --deep --force --options runtime --sign "<DEVELOPER_ID>" \
  "dist/AutoResumeAgent.app"
xcrun notarytool submit "<archive>" --keychain-profile "<PROFILE>" --wait
xcrun stapler staple "dist/AutoResumeAgent.app"
```

Verify with `codesign --verify --deep --strict --verbose=2` and
`spctl --assess --type execute --verbose=4`. Notarization and stapling are
external release tasks; they are not required for local tests.

## Release wording

When unsigned, say so explicitly in release notes and the checklist. Do not
claim that macOS Gatekeeper or Windows SmartScreen will accept the artifact
without user approval. Signing keys, certificates, and notarization credentials
must remain outside the repository and CI logs.
