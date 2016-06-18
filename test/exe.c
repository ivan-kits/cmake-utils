#include "shared/shared.h"
#include "static/static.h"
#include <stdio.h>

int main() {
	printf("%s\n", shared_get_string());
	printf("%s\n", static_get_string());
}
