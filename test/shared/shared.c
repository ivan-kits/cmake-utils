#ifndef SHARED_C
#define SHARED_C

#include "shared.h"


const char *shared_get_string() {
	return "This is a C string from a shared library.";
}


#endif
