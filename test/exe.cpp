extern "C" {
#include "shared/shared.h"
#include "static/static.h"
}

#if defined(NONE) || defined(SYSTEM)
#if defined(NONE)
#include <stdio.h>
#elif defined(SYSTEM)
#include <cstdio>
#endif

int main() {
	printf("%s\n", shared_get_string());
	printf("%s\n", static_get_string());
}

#else // neither none nor system

#include "shared/shared.hpp"
#include "static/static.hpp"
#include <iostream>

int main() {
	std::cout
		<< shared_get_string() << std::endl
		<< static_get_string() << std::endl
		<< Shared().GetString() << std::endl
		<< Static().GetString() << std::endl;
}

#endif
