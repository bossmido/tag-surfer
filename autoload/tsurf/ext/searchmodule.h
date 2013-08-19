#ifndef SEARCHMODULE_H
#define SEARCHMODULE_H

#include <Python.h>
#include <ctype.h>

/*
 * To compute the similarity between two strings given `haystack` and the 
 * positions where `needle` matches in `haystack`.
 *
 * Returns a number that indicate the similarity between the two strings.
 * The lower it is, the more similar the two strings are.
 *
 */
float similarity(const char*, PyObject*, int);

#endif
