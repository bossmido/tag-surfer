/* 
 * searchmodule.c 
 *
 * C version of the algorithms found in `tsurf.utils.search`.
 *
 */

#include "searchmodule.h"


static PyObject *
py_fuzzy_search(PyObject *self, PyObject *args)
{
    const char *needle;
    const int needle_len;
    const char *haystack;
    const int haystack_len;

    if (!PyArg_ParseTuple(args, "s#s#", &needle, &needle_len, &haystack, &haystack_len))
        return NULL;

    if (needle_len == 0) {
        return Py_BuildValue("(i,())", -1);        
    }

    PyObject *positions = PyList_New(0);
    char c1, c2;

    PyObject *pos;
    int needle_idx = 0;
    for (int i = 0; i < haystack_len; i++)
    {
        if (needle_idx == needle_len)
            break;

        c1 = tolower(needle[needle_idx]);
        c2 = tolower(haystack[i]);
        if (c1 == c2) {
            pos = Py_BuildValue("i", i);
            PyList_Append(positions, pos);
            Py_DECREF(pos);
            needle_idx++;
        }
    }

    if (needle_idx == needle_len) {
        PyObject *tpos = PySequence_Tuple(positions);
        Py_DECREF(positions);
        return Py_BuildValue("(f,N)", compute_score(haystack, tpos), tpos);
    } else {
        // no match
        return Py_BuildValue("(i,())", -1);
    }
}


static PyObject *
py_smart_search(PyObject *self, PyObject *args) 
{
    const char *needle;
    const int needle_len;
    const char *haystack;
    const int haystack_len;

    if (!PyArg_ParseTuple(args, "s#s#", &needle, &needle_len, &haystack, &haystack_len))
        return NULL;

    // Check if `haystack` contains only uppercase letters.
    // If this is the case, then we do not consider an uppercase letter
    // as the start of a new token.
    int haystack_is_upper = 1;
    for (int i = 0; i < haystack_len; i++) {
        if (!isupper(haystack[i]))
            haystack_is_upper = 0;
    }        

    return _smart_search(needle, needle_len, haystack, haystack_len, 
        haystack_is_upper, -1, PyList_New(0));
}

PyObject*
_smart_search(const char *needle, int needle_len, const char *haystack, int haystack_len,
    int haystack_is_upper, int start, PyObject *positions)
{
    if (needle_len == 0 || start >= haystack_len-1) {
        return Py_BuildValue("(i,())", -1);        
    }

    int a_token_starts = 1;
    int last_successful_match = -1;

    char c1, c2;
    PyObject *pos;
    int needle_idx = 0;
    for (int i = 0; i < haystack_len; i++)
    {
        if (i <= start)
            continue;

        if (needle_idx == needle_len)
            break;

        Py_ssize_t positions_len = PyList_Size(positions);
        c1 = tolower(needle[needle_idx]);
        c2 = tolower(haystack[i]);

        int prev_char_matched = 0;
        if (positions_len && i-1 == last_successful_match)
            prev_char_matched = 1;
        int cond = positions_len == 0 || prev_char_matched || a_token_starts;
        if (c1 == c2 && cond) {
            pos = Py_BuildValue("i", i);
            PyList_Append(positions, pos);
            Py_DECREF(pos);
            last_successful_match = i;
            needle_idx++;
        }

        a_token_starts = 0;

        int cond1 = c2 == '_' || c2 == '-' || c2 == '.';
        int cond2 = i < haystack_len-1 && isupper(haystack[i+1]);
        if (cond1 || (cond2 && !haystack_is_upper))
            a_token_starts = 1;
    }

    if (needle_idx == needle_len) {
        PyObject *tpos = PySequence_Tuple(positions);
        Py_DECREF(positions);
        return Py_BuildValue("(f,N)", compute_score(haystack, tpos), tpos);
    } else if (last_successful_match > -1) {
        return _smart_search(needle, needle_len, haystack, haystack_len, 
            haystack_is_upper, last_successful_match, positions);
    } else {
        return Py_BuildValue("(i,())", -1);
    }
}


float 
compute_score(const char *haystack, PyObject *positions) 
{
    Py_ssize_t pos_len = PyTuple_Size(positions);

    if (pos_len == 0)
        return -1;

    int n = 0;
    int sum_diffs = 0;
    int sum_positions = 0;
    // Generate all `positions` combinations for k = 2
    float x1, x2;
    for (int i = 0; i < pos_len; i++) {
        x1 = PyFloat_AsDouble(PyTuple_GetItem(positions, i)); 
        sum_positions += x1;
        for (int j = i; j < pos_len; j++) {
            if (j != i) {
                x2 = PyFloat_AsDouble(PyTuple_GetItem(positions, j)); 
                sum_diffs += abs(x1-x2);
                n += 1;
            }
        }
    }             

    float ratio = strlen(haystack)*1.0 / pos_len;

    if (n > 0)
        return sum_diffs*1.0/n + sum_positions*1.0/pos_len + ratio;
    else
        return PyFloat_AsDouble(PyTuple_GetItem(positions, 0)) + ratio;
}


static PyMethodDef searchMethods[] = {
    {"fuzzy_search", py_fuzzy_search, METH_VARARGS,
    "To returns the positions at which `needle` matches in `haystack` using fuzzy search."},
    {"smart_search", py_smart_search, METH_VARARGS,
    "To returns the positions at which `needle` matches in `haystack` using smart search."},
    {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
initsearch(void)
{
    (void) Py_InitModule("search", searchMethods);
}
