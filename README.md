# steam_workshop_discord

A python program that polls the Steam workshop of specified games for new mods and posts them to a Discord channel using a webhook.

![grafik](https://user-images.githubusercontent.com/14299449/77251258-ada86f80-6c4d-11ea-9fcf-7ec6f134b17c.png)

## Dependencies

* Python 3.5+
* `toml` (`python3 -m pip install toml`)

## Setup

1. Generate a [Steam Web API key](https://steamcommunity.com/dev/apikey) and one (or more) [Discord webhook(s)](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

2. Determine the Steam ID of the games whose workshop pages you are interested in.

3. Create a copy of `config.toml.template` named `config.toml`, open it with a text editor, fill out the information.

4. Create a cron job (or find a dfferent scheduler) that regularly runs the script.

## Inner workings

The script maintains a list of all the mods it has posted to each channel.
Whenever it is run, it determines the workshop pages it needs to fetch, requests the ten latest mods from each page.
For each channel, if the channel has no recorded mods, those mods are listed as recorded. Otherwise, the new mods are filtered, and author+mod information
is requested. Using mod and author information, a message is assembled, which is then posted to each channel that needs it.
Only upon a successful (HTTP 204) request, the mod is recorded as posted.

## Compatibility policy

New versions of this script may break compatibility with previous deployments. For updates to running deployments,
the author recommends configuring the new deployment without a `known_mods` file, running the old version one final time,
then running the new deployment once immediately. As of the current version, the script will never post mods to a channel if the
channel hasn't been recorded in `known_mods`, so there will be no duplicate posts.


## License

Licensed under either of

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any
additional terms or conditions.