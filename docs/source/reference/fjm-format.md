# The `.fjm` binary format

`.fjm` ("Flip-Jump Memory") is the assembled output of `fj`. It is a flat image of the program's initial memory: a header, a table of segments, and a blob of memory-words. The interpreter loads it into a word-addressable memory and starts executing at address `0`.

You produce one with `fj --asm -o out.fjm …` and run it with `fj --run out.fjm` — see [the `fj` command-line tool](cli.md).

## File layout

The whole file is little-endian. In C-struct terms (straight from the assembler's source):

```c
struct {
    u16 fj_magic;       // 'F' + 'J'<<8  (0x4a46)
    u16 word_size;      // bits per memory-word, a.k.a. "w"
    u64 version;
    u64 segment_num;
    {                   // only for versions > 0
        u64 flags;
        u32 reserved;   // always 0
    }
    struct segment {
        u64 segment_start;  // in memory-words (w bits each)
        u64 segment_length; // in memory-words
        u64 data_start;     // offset into `data`, in memory-words
        u64 data_length;    // in memory-words
    } segments[segment_num];
    u8  data[];         // the words themselves (compressed in some versions)
} fjm_file;
```

### Header

| Field | Type | Notes |
|---|---|---|
| `fj_magic` | `u16` | Always `0x4a46` (the bytes `F`, `J`). A mismatch means it isn't a `.fjm` file. |
| `word_size` | `u16` | Memory width `w` — `8`, `16`, `32`, or `64`. Set by `fj -w`. |
| `version` | `u64` | Format version (see below). |
| `segment_num` | `u64` | Number of segment descriptors that follow. |
| `flags` | `u64` | Default unpacking/running flags. Set by `fj -f`. Present only when `version > 0`. |
| `reserved` | `u32` | Must be `0`. Present only when `version > 0`. |

## Versions

| Value | Name | What's different |
|---|---|---|
| `0` | Base | The minimal structure — no `flags`/`reserved` block. |
| `1` | Normal | Adds the `flags` and `reserved` header fields. |
| `2` | RelativeJump | Compress-friendly: jump targets in `data` are stored **relative** to their own address. |
| `3` | Compressed | Same as version 2, but `data` is LZMA2-compressed. |

`fj` defaults to **3 (Compressed)** when you save with `-o`, and **1 (Normal)** otherwise. Choose explicitly with `fj -v`.

## Segments

Each segment maps a run of memory-words. All four fields are counted in memory-words, not bytes:

- `segment_start` — where in memory this segment is placed.
- `segment_length` — how many words the segment spans.
- `data_start` — where its words begin inside the `data` blob.
- `data_length` — how many words are actually stored.

When `data_length < segment_length`, the trailing words are **zero-filled** — that's how large zero-initialised regions (stacks, lookup tables, `reserve`d space) stay cheap: they cost a descriptor, not megabytes of zeros. The reader fills small gaps explicitly and tracks larger zero ranges separately so it never materialises millions of zero entries.

## How it's loaded and run

`fj --run` reads the file like this (the same loading the [online IDE](../tools/ide.md) does to run your program):

1. Parse the header, validate the magic, version and `reserved` fields.
2. Read `segment_num` segment descriptors.
3. Take the `data` blob — LZMA2-decompress it first for version 3.
4. Unpack it into `word_size`-bit words.
5. For versions 2 and 3, rebuild each jump word by adding its own address back to the stored relative offset.
6. Lay the words out per the segment table (zero-filling the gaps).

The result is a dictionary mapping word-address → word-value: the interpreter's initial memory. From there it just runs the one FlipJump instruction over and over — see [The FlipJump Instruction](../language/instruction.md).

## See also

- [The `fj` command-line tool](cli.md) — produces and runs `.fjm` files.
- [Directives](../language/directives.md) — `segment`, `reserve` and `wflip`, which shape the segment table.
- [The FlipJump Instruction](../language/instruction.md) — what the loaded words actually do.
