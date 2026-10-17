# Repository guidance

- This repository distributes portable skills and helpers, not the maintainer's theme products.
- Keep account IDs, private workspace paths, browser sessions, keys, copyrighted templates and artwork out of the repository.
- Maintain independent installability of both skills. Do not import files outside an installed skill directory.
- New commands must be testable offline and must not publish to stores during tests.
- Preserve the separation between structural checks, signature checks, visual inspection and real KakaoTalk application.
- Publisher scripts prepare files and maintain a journal; browser tools perform the actual authorized upload.
- Never repeat a final submission while its result is unresolved.
- Windows child processes must avoid opening terminals or stealing focus. Use direct executables, CREATE_NO_WINDOW or windowsHide, noninteractive stdin and captured logs.
- Run python -m unittest discover -s tests -v after executable changes.
- Keep README installation and usage examples consistent with actual commands.
