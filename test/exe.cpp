extern "C" {
#include "shared/shared.h"
#include "static/static.h"
}
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
