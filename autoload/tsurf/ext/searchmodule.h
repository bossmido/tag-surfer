#ifndef SEARCHMODULE_H
#define SEARCHMODULE_H

#include <Python.h>
#include <ctype.h>

PyObject* _smart_search(const char*, int, const char*, int, int, int, PyObject*);

float compute_score(const char*, PyObject*);

#endif
