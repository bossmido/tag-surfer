/* 
 * searchmodule.c 
 *
 * C version of `tsurf.utils.search`.
 *
 * TODO: Use a struct instead of a python dictionary for
 * storing info about a possible match.
 *
 */

#include "searchmodule.h"


static char py_search_doc[] = "To search for `needle` in `haystack`.\n"
    "Returns a tuple of two elements: a number and another tuple."
    "The number is a measure of the similarity between `needle` and "
    "`haystack`, whereas the other tuple contains the positions where "
    "the match occurs in `haystack`.";

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

    // If `haystack` has only uppercase characters then it makes no sense
    // to treat an uppercase letter as a word-boundary character
    int uppercase_is_word_boundary = 0;
    // `max_possible_matches` indicate the maximum number of matches
    // of `needle` that can occur in `haystack`
    int max_possible_matches = 0;

    for (int i = 0; i < haystack_len; i++) {

        if (haystack[i] >= 97 && haystack[i] <= 122)
            // non-uppercase letter is found
            uppercase_is_word_boundary = 1;

        if (match(haystack[i], needle[0], smart_search))
            // for every character in `haystck` that match with the 
            // first cahracter in `needle` we may guess that a 
            // possible match could happen
            max_possible_matches++;
    }

    if (max_possible_matches == 0)
        return Py_BuildValue("(i,())", -1);
    
    // `possible_matches` keeps track of all possible matches of `needle`
    // along `haystack`
    PyObject *possible_matches = PyList_New(max_possible_matches);  // new ref
    int possible_matches_idx = 0;

    for (int i = 0; i < haystack_len; i++) {

        if (match(haystack[i], needle[0], smart_search)) {
            // add a new possible match if we encounter along `haystack`
            // a possible "start of match" for `needle`
            PyObject *possible_match = PyDict_New();  // new ref
            PyDict_SetItemString(possible_match, 
                    "needle_idx", Py_BuildValue("i", 0));
            PyDict_SetItemString(possible_match, 
                    "boundaries_count", Py_BuildValue("i", 0));
            PyDict_SetItemString(possible_match, 
                    "positions", PyList_New(0));
            // Note: PyList_SetItem don't increment the reference count
            PyList_SetItem(possible_matches, possible_matches_idx, possible_match);  
            possible_matches_idx++;
        }

        // update each possible match

        for (int j = 0; j < possible_matches_idx; j++) {
            
            PyObject *possible_match = PyList_GetItem(possible_matches, j);  // borrowed ref
            assert(PyDict_Check(possible_match));

            int needle_idx = PyInt_AsLong(
                    PyDict_GetItemString(possible_match, "needle_idx"));

            int boundaries_count = PyInt_AsLong(
                    PyDict_GetItemString(possible_match, "boundaries_count"));

            PyObject *positions = PyDict_GetItemString(possible_match, "positions");  // borrowed ref
            assert(PyList_Check(positions));

            if (needle_idx == needle_len)
                continue;

            if (match(haystack[i], needle[needle_idx], smart_search)) {
                PyObject *pos = Py_BuildValue("i", i);  // new ref
                PyList_Append(positions, pos);
                Py_DECREF(pos);

                if ((uppercase_is_word_boundary && isupper(haystack[i])) || i == 0 || 
                    (i > 0 && (haystack[i-1] == '-' || haystack[i-1] == '_')))
                    boundaries_count++;

                needle_idx++;
            }

            // update values for the possible_match
            PyDict_SetItemString(possible_match, 
                    "needle_idx", Py_BuildValue("i", needle_idx));
            PyDict_SetItemString(possible_match, 
                    "boundaries_count", Py_BuildValue("i", boundaries_count));

        }
    }

    PyObject *best_positions = NULL;
    float best_similarity = .0;

    Py_ssize_t possible_matches_len = PyList_Size(possible_matches);
    for (int i = 0; i < possible_matches_len; i++) {

        PyObject *match = PyList_GetItem(possible_matches, i);  // borrowed ref
        assert(PyDict_Check(match));

        int needle_idx = PyInt_AsLong(
                PyDict_GetItemString(match, "needle_idx"));

        if (needle_idx == needle_len) {

            PyObject *positions = PyDict_GetItemString(match, "positions");
            assert(PyList_Check(positions));

            int boundaries_count = PyInt_AsLong(
                    PyDict_GetItemString(match, "boundaries_count"));

            if (best_positions == NULL) {
                best_positions = positions; 
                best_similarity = similarity(haystack, positions, boundaries_count);
            } else {
                float s = similarity(haystack, positions, boundaries_count);
                if (s < best_similarity) {
                    best_positions = positions;
                    best_similarity = s;
                }
            }
        }
    }

    if (best_positions != NULL) {
        PyObject *tpos = PySequence_Tuple(best_positions); // new ref
        Py_DECREF(possible_matches);   
        return Py_BuildValue("(f,N)", best_similarity, tpos);
    } else {
        // no match found
        Py_XDECREF(possible_matches);
        return Py_BuildValue("(i,())", -1);
    }
}


int
match(char c1, char c2, int smart_search) 
{
    // smart_search == 1: consider the case only if `c2` is uppercase.
    if (smart_search && isupper(c2))
        return c1 == c2;
    else
        return tolower(c1) == tolower(c2);
}


float 
similarity(const char *haystack, PyObject *positions, int boundaries_count) 
{
    assert(PyList_Check(positions));

    Py_ssize_t positions_len = PyList_Size(positions);
    if (positions_len == 0)
        return -1;

    int n = 0;
    float diffs_sum = .0;
    // Generate all `positions` combinations for k = 2 and
    // sum the absolute difference computed for each one.
    float x1, x2;
    for (int i = 0; i < positions_len; i++) {
        x1 = PyFloat_AsDouble(PyList_GetItem(positions, i)); 
        for (int j = i; j < positions_len; j++) {
            if (j != i) {
                x2 = PyFloat_AsDouble(PyList_GetItem(positions, j)); 
                diffs_sum += abs(x1-x2);
                n += 1;
            }
        }
    }             

    float len_ratio = strlen(haystack)*1.0 / positions_len;  
    if (boundaries_count)
        len_ratio /= (boundaries_count + 1);

    if (n > 0) {
        return diffs_sum/n + len_ratio;
    } else {
        // `positions_len == 1`
        return PyFloat_AsDouble(PyList_GetItem(positions, 0)) + len_ratio;
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
