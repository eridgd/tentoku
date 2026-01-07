# JMDict Dictionary Attribution

This module uses the JMDict/EDICT dictionary files for Japanese word lookups.

## Dictionary Data License

The JMDict dictionary data is licensed under the **Creative Commons Attribution-ShareAlike 4.0 International License** (CC BY-SA 4.0).

## Attribution

This software uses the JMDict/EDICT dictionary files, which are the property of the Electronic Dictionary Research and Development Group (EDRDG).

**JMDict Project**: https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project

**Electronic Dictionary Research and Development Group (EDRDG)**: https://www.edrdg.org/

**EDRDG License Statement**: https://www.edrdg.org/edrdg/licence.html

**Copyright**: James William BREEN and The Electronic Dictionary Research and Development Group

**License**: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- Full license: https://creativecommons.org/licenses/by-sa/4.0/
- Legal code: https://creativecommons.org/licenses/by-sa/4.0/legalcode

**License File**: See [JMDICT_LICENSE.txt](JMDICT_LICENSE.txt) in this package for the complete license information.

## License Terms

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

No additional restrictions — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

## How This Module Uses JMDict

This module automatically downloads the JMDict XML file from the official EDRDG source (`https://www.edrdg.org/pub/Nihongo/JMdict_e.gz`) and converts it to a SQLite database for efficient lookups. The database is built locally and stored in the module's data directory.

The dictionary data is not included in this software package - it is downloaded separately by users when they first use the module.

## License Compatibility

While this software (the Python code) is licensed under GPL-3.0-or-later, the JMDict dictionary data remains under CC BY-SA 4.0. When distributing this software with the database, both licenses apply to their respective components.

