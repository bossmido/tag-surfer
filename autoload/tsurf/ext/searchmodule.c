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
    const int smart_case;

    if (!PyArg_ParseTuple(args, "s#s#i", 
            &needle, &needle_len, &haystack, &haystack_len, &smart_case))
        return NULL;

    if (needle_len == 0) {
        return Py_BuildValue("(i,())", -1);        
    }

    // If `haystack` has only uppercase characters then it makes no sense
    // to treat an uppercase letter as a word-boundary character
    int uppercase_is_word_boundary = 0;
    for (int i = 0; i < haystack_len; i++) {
        if (haystack[i] >= 97 && haystack[i] <= 122)
            // non-uppercase letter is found
            uppercase_is_word_boundary = 1;
    }

    PyObject *best_positions = Py_BuildValue("()");
    float best_similarity = -1;    

    // `matchers` keeps track of all matches of `needle` in `haystack`
    PyObject *matchers = PyList_New(1);  // new ref

    // add the first matcher
    PyObject *matcher = PyDict_New();  // new ref
    PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", 0));
    PyDict_SetItemString(matcher, "consumed", PyList_New(0));  // list of characters
    PyDict_SetItemString(matcher, "boundaries", PyList_New(0));  // list of numbers
    PyDict_SetItemString(matcher, "positions", PyList_New(0));  // list of numbers
    // Note: PyList_SetItem don't increment the reference count
    PyList_SetItem(matchers, 0, matcher);  // PyList_SetItem do not increment the ref counter  

    PyObject *needle_pyobj = Py_BuildValue("s", needle);  // new ref    
    Py_ssize_t needle_pyobj_len = PySequence_Length(needle_pyobj);

    for (int i = 0; i < haystack_len; i++) {

        // create forks of current matches if needed

        PyObject *matcher;
            
        Py_ssize_t matchers_len = PyList_Size(matchers);
        for (int j = 0; j < matchers_len; j++) {

            // get matchers[j] and its values
            matcher = PyList_GetItem(matchers, j);
            /*assert(PyDict_Check(matcher));*/
            PyObject *consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            PyObject *positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            PyObject *boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/

            // check if the current character in `haystack` has been matched 
            // before by the matchers[j]. If so, we crate a fork of matcher[j].
            int idx = -1;
            // check correctness with smart case
            for (int k = 0; k < PyList_Size(consumed); k++) {
                int c = PyInt_AsLong(PyList_GetItem(consumed, k));
                if (tolower(haystack[i]) == c) { 
                    idx = k;
                    break;
                }
            }
            if (idx >= 0) {           
                PyObject *slice = PySequence_GetSlice(needle_pyobj, idx, needle_pyobj_len);  // new ref
                if (PySequence_Length(slice) <= haystack_len - i) {
                    // create a new fork
                    PyObject *fork = PyDict_New();  // new ref
                    PyDict_SetItemString(fork, "needle_idx", Py_BuildValue("i", idx));
                    PyDict_SetItemString(fork, "consumed", PySequence_GetSlice(consumed, 0, idx));
                    PyDict_SetItemString(fork, "boundaries", PySequence_GetSlice(boundaries, 0, idx));
                    PyDict_SetItemString(fork, "positions", PySequence_GetSlice(positions, 0, idx));
                    // append the new fork to matchers pool
                    PyList_Append(matchers, fork);  // PyList_append increment the ref counter
                    Py_DECREF(fork);
                }
                Py_DECREF(slice);
            }
        }

        // update each matcher
        
        PyObject *pos, *c;

        for (int j = 0; j < PyList_Size(matchers); j++) {
            
            PyObject *matcher = PyList_GetItem(matchers, j);  // borrowed ref
            /*assert(PyDict_Check(matcher));*/

            int needle_idx = PyInt_AsLong(PyDict_GetItemString(matcher, "needle_idx"));
            PyObject *consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            PyObject *positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            PyObject *boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/

            if (needle_idx == needle_len)
                continue;

            int cond;
            if (smart_case && isupper(needle[needle_idx]))
                cond = haystack[i] == needle[needle_idx];
            else
                cond = tolower(haystack[i]) == tolower(needle[needle_idx]);           

            if (cond) {

                if ((uppercase_is_word_boundary && isupper(haystack[i])) || i == 0 || 
                    (i > 0 && (haystack[i-1] == '-' || haystack[i-1] == '_'))) {
                    pos = Py_BuildValue("i", 1);  // new ref
                    PyList_Append(boundaries, pos);
                } else {
                    pos = Py_BuildValue("i", 0);  // new ref
                    PyList_Append(boundaries, pos);
                }
                Py_DECREF(pos);

                pos = Py_BuildValue("i", i);  // new ref
                PyList_Append(positions, pos);
                Py_DECREF(pos);

                c = Py_BuildValue("i", tolower(needle[needle_idx]));  // new ref
                PyList_Append(consumed, c);
                Py_DECREF(c);

                needle_idx++;
                PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", needle_idx));

                if (needle_idx == needle_len) {
                    int boundaries_count = 0;
                    for (int k = 0; k < PyList_Size(boundaries); k++) {
                        if (PyInt_AsLong(PyList_GetItem(boundaries, k)))
                            boundaries_count++;
                    }
                    float s = similarity(haystack_len, positions, boundaries_count);
                    if (best_similarity < 0 || s < best_similarity) {
                        best_similarity = s;
                        Py_DECREF(best_positions);  // TODO: correct right ??
                        best_positions = PySequence_Tuple(positions);
                    }
                }
            }
        }
    }
    Py_DECREF(needle_pyobj);
    Py_XDECREF(matchers);
    return Py_BuildValue("(f,N)", best_similarity, best_positions);
}


float 
similarity(int haystack_len, PyObject *positions, int boundaries_count) 
{
    /*assert(PyList_Check(positions));*/

    Py_ssize_t positions_len = PyList_Size(positions);
    if (positions_len == 0)
        return -1;

    int n = 0;
    float diffs_sum = .0;
    int contiguous_sets = 1;

    // Generate all `positions` combinations for k = 2 and
    // sum the absolute difference computed for each one.
    float x1, x2, prev;
    for (int i = 0; i < positions_len; i++) {

        x1 = PyFloat_AsDouble(PyList_GetItem(positions, i)); 

        if (i > 0) {
            prev = PyFloat_AsDouble(PyList_GetItem(positions, i-1)); 
            if (prev != x1 - 1)
                contiguous_sets++;
        }

        for (int j = i; j < positions_len; j++) {
            if (j != i) {
                x2 = PyFloat_AsDouble(PyList_GetItem(positions, j)); 
                diffs_sum += abs(x1-x2);
                n += 1;
            }
        }
    }             

    if (n > 0) {
        return diffs_sum/n * contiguous_sets / (boundaries_count ? boundaries_count*1.0 : 1.0);
    } else {
        // `positions_len == 1`
        return (PyFloat_AsDouble(PyList_GetItem(positions, 0)) / 
                boundaries_count ? boundaries_count*1.0 : 1.0);
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
