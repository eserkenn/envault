# envault

> A CLI tool for managing and encrypting environment variables across multiple deployment targets.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended for CLI tools):

```bash
pipx install envault
```

---

## Usage

Initialize a new vault in your project:

```bash
envault init
```

Add and encrypt an environment variable:

```bash
envault set API_KEY "my-secret-key" --target production
```

Inject variables into a running process:

```bash
envault run --target production -- python app.py
```

Export decrypted variables to a `.env` file:

```bash
envault export --target staging --output .env.staging
```

Manage multiple deployment targets:

```bash
envault targets list
envault targets add staging
envault targets remove old-env
```

---

## Configuration

envault stores encrypted secrets in a `.envault` directory at your project root. Add `.envault/keys/` to your `.gitignore` and safely commit `.envault/vault.json`.

---

## License

[MIT](LICENSE) © envault contributors