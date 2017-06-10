from libc.setjmp cimport jmp_buf
from cpython.object cimport PyObject
cimport callback

cdef extern from "ccallback.h":
    ctypedef struct ccallback_signature_t:
        char *signature
        int value

    ctypedef struct ccallback_t:
        void *c_function
        PyObject *py_function
        void *user_data
        ccallback_signature_t *signature        
        jmp_buf error_buf
        ccallback_t *prev_callback

        # Unused variables that can be used by the thunk etc. code for any purpose
        long info
        void *info_p

    ccallback_t *ccallback_obtain()
    int ccallback_prepare(ccallback_t *callback, ccallback_signature_t *sigs,
                          object func, int flags) except -1
    void ccallback_release(ccallback_t *callback)


cdef callback_t * callback_obtain():
    return <callback_t *>ccallback_obtain()


cdef int callback_prepare(callback_t *callback, callback_signature_t *sigs,
                        object func, int flags) except -1:
    return ccallback_prepare(<ccallback_t *>callback, <ccallback_signature_t *>sigs, func, flags)


cdef void callback_release(callback_t *callback):
    ccallback_release(<ccallback_t *>callback)
