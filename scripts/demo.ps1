$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
resume-cli --help
resume-cli parse examples/resume.pdf
resume-cli extract examples/resume.pdf --mock
resume-cli score examples/resume.pdf --jd examples/jd.txt --mock --output score.json
python -m pytest -q
