/* 
 * searchmodule.c 
 *
 * C version of `tsurf.utils.search`.
 *
 */

#include "searchmodule.h"


static char py_search_doc[] = "To search for `needle` in `haystack`.\n"
    "Returns a tuple of two elements: a number and another tuple."
    "The number is a measure of the similarity between `needle` and `haystack`,"
    "whereas the other tuple contains the positions where the match occurs in `haystack`.";

static PyObject *
py_search(PyObject *self, PyObject *args)
{
    const char *needle;
    const int needle_len;
    const char *haystack;
    const int haystack_len;
    const int smart_search;

    if (!PyArg_ParseTuple(args, "s#s#i", 
            &needle, &needle_len, &haystack, &haystack_len, &smart_search))
        return NULL;

    if (needle_len == 0) {
        return Py_BuildValue("(i,())", -1);        
    }

    // `positions` is a list of positions where any characters in `needle`
    // matches in `haystack`
    PyObject *positions = PyList_New(0);
    // `boundaries_count` is the count of how many characters in `positions`
    // are word boundaries
    int boundaries_count = 0;

    // If `haystack` has only uppercase characters then it makes no sense
    // to treat an uppercase letter as a word-boundary character
    int uppercase_is_word_boundary = 0;
    for (int i = 0; i < haystack_len; i++) {
        char c = haystack[i];
        if (c >= 97 && c <= 122)  // non-uppercase letter
            uppercase_is_word_boundary = 1;
    }

    PyObject *pos;
    int cond;
    int needle_idx = 0;
    for (int i = 0; i < haystack_len; i++)
    {
        if (needle_idx == needle_len)
            break;

        // smart search: consider the case only if the character of `needle`
        // is uppercase
        if (smart_search && isupper(needle[needle_idx]))
            cond = haystack[i] == needle[needle_idx];
        else
            cond = tolower(haystack[i]) == tolower(needle[needle_idx]);

        if (cond) {
            pos = Py_BuildValue("i", i);
            PyList_Append(positions, pos);

            if ((uppercase_is_word_boundary && isupper(haystack[i])) || i == 0 || 
                (i > 0 && (haystack[i-1] == '-' || haystack[i-1] == '_')))
                boundaries_count++;

            Py_DECREF(pos);
            needle_idx++;
        }
    }

    if (needle_idx == needle_len) {
        PyObject *tpos = PySequence_Tuple(positions);
        Py_DECREF(positions);
        return Py_BuildValue("(f,N)", 
                similarity(haystack, tpos, boundaries_count), tpos);
    } else {
        // no match
        return Py_BuildValue("(i,())", -1);
    }
}


float 
similarity(const char *haystack, PyObject *positions, int boundaries_count) 
{
    Py_ssize_t positions_len = PyTuple_Size(positions);
    if (positions_len == 0)
        return -1;

    int n = 0;
    int diffs_sum = 0;
    int positions_sum = 0;
    // Generate all `positions` combinations for k = 2
    float x1, x2;
    for (int i = 0; i < positions_len; i++) {
        x1 = PyFloat_AsDouble(PyTuple_GetItem(positions, i)); 
        positions_sum += x1;
        for (int j = i; j < positions_len; j++) {
            if (j != i) {
                x2 = PyFloat_AsDouble(PyTuple_GetItem(positions, j)); 
                diffs_sum += abs(x1-x2);
                n += 1;
            }
        }
    }             

    float len_ratio = strlen(haystack)*1.0 / positions_len;    
    if (boundaries_count)
        len_ratio /= (boundaries_count + 1);

    if (n > 0) {
        return diffs_sum*1.0/n + positions_sum*1.0/positions_len + len_ratio;
    } else {
        // `positions_len == 1`
        return PyFloat_AsDouble(PyTuple_GetItem(positions, 0)) + len_ratio;
    }
}


static PyMethodDef searchMethods[] = {
    {"search", py_search, METH_VARARGS, py_search_doc},
    {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
initsearch(void)
{
    (void) Py_InitModule("search", searchMethods);
}
