# Hypermeme Templates

Meme templates and video memes that imgflip doesn't have yet, each with a description of what's in the picture and when people use it, so they can be found by what they mean and not only by name.

[Hypermeme](https://github.com/alexisbcz/hypermeme) reads `index.json` from this repository. Anything else can too:

```sh
curl -s https://raw.githubusercontent.com/alexisbcz/hypermeme-templates/main/index.json \
  | jq '.templates[] | select((.name + " " + (.aliases|join(" ")) + " " + .description + " " + (.tags|join(" "))) | test("coffee"; "i")) | .imageURL'
```

## Layout

```
templates/
  paris-cafe-riot/
    image.jpg
    template.json
  terry-davis-suck-it-up/
    image.jpg        the poster: shown in search, and what captions are placed on
    video.mp4
    template.json
index.json        all templates in one file, built by scripts/build.py
```

## template.json

| Field | |
| --- | --- |
| `name` | The name most people use. |
| `aliases` | Other names, and the phrases someone would type looking for it. |
| `description` | What's in the picture, plainly. |
| `usage` | What the meme means and how it's usually captioned. |
| `tags` | Single words: mood, subject, place. |
| `image`, `width`, `height` | The image file in the same folder and its size in pixels. |
| `captionStrip` | `true` when the meme is captioned in a white strip above the image, as on X. |
| `video`, `duration` | For a video meme: the MP4 in the same folder (H.264, under 15 MB) and its length in seconds. `image` is then its poster frame. |
| `boxes` | Text boxes on the image, in Hypermeme's `TextBox` format: `x`, `y`, `width`, `height` as fractions of the image, plus optional `rotation`, `font`, `color`, `outline`, `allCaps`, `align`, `verticalAlign`, `shadow`, `maxFontSize`. |
| `source` | Where it was first seen: `url`, `author`, `date`, and an `example` caption. |

The folder name is the template's id.

## Adding a template

```sh
python3 scripts/add.py https://x.com/user/status/123 some-id   # downloads the image or video, fills in source
$EDITOR templates/some-id/template.json                        # name, aliases, description, usage, tags
python3 scripts/build.py                                       # checks everything, rebuilds index.json
```

For a post with a video, `add.py` shrinks it with ffmpeg and saves its first second as the poster. `--start` and `--length` (in seconds) cut a long one down to the part worth keeping.

CI fails a pull request whose templates don't check out or whose `index.json` wasn't rebuilt.

Images belong to their creators. They're collected here for captioning and commentary; open an issue to have one removed.
