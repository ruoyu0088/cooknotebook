# -*-cython-*-
from libc.setjmp cimport jmp_buf
from cpython.object cimport PyObject

ctypedef struct callback_signature_t "callback_signature_t":
    char *signature
    int value

ctypedef struct callback_t "callback_t":
    void *c_function
    PyObject *py_function
    void *user_data
    callback_signature_t *signature   
    jmp_buf error_buf
    callback_t *prev_callback

    # Unused variables that can be used by the thunk etc. code for any purpose
    long info
    void *info_p


cdef callback_t * callback_obtain()
cdef int callback_prepare(callback_t *callback, callback_signature_t *sigs,
                        object func, int flags) except -1
cdef void callback_release(callback_t *callback)
