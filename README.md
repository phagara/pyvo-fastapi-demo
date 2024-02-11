# pyvo-fastapi-demo

Smol FastAPI demo app for a Pyvo Brno talk
(see [event details](https://pyvo.cz/brno-pyvo/2023-10/)
and [video recording](https://www.youtube.com/watch?v=FiVXISPeKO4)).

## How to run the app, tests, linters, and code formatters

First, ensure you have [Hatch](https://hatch.pypa.io/latest/) installed:

```
pip install hatch
```

### Run the app

```
hatch run -- uvicorn pyvo_fastapi_demo.main:app --reload
```

### Run unit tests and report test coverage

```
hatch run test-cov
hatch run cov-report
```

### Run linters

```
hatch run lint:all
```

### Run code formatters

```
hatch run lint:fmt
```

## License

`pyvo-fastapi-demo` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
