#ifndef SEARCHMODULE_H
#define SEARCHMODULE_H

#include <Python.h>
#include <ctype.h>
#include <limits.h>


/*
 * To check if the two character c1 and c2 are equals.
 *
 * If the last argument == 1, the case is considered only if `c2` is uppercase.
 *
 */
int match(char, char, int); 


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
