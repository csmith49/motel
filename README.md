# Motel

The *place to be* for all development on **MOT**if **E**numeration (**MOTE**).

## Goal of the **MOTE** Project

Entity extraction from small numbers of positive examples.

## Building the Source

Motel relies on Python 3 for most glue code, and OCaml for performant enumeration. For the OCaml portions, all that is needed is an up-to-date version of [OPAM](https://opam.ocaml.org).

## Structure of this Repository

The Mote submodule contains all the OCaml code. Depending on your version of git, you may have to initialize it separately. The Makefile should handle that for you, though.

Motel can be included, or used as a command-line script.

## Documentation

Relies on [numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) doc-strings.
