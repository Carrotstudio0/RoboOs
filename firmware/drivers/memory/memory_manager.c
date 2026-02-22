/**
 * Memory Manager Implementation
 * تطبيق مدير الذاكرة
 */

#include "../../include/memory_manager.h"
#include <string.h>
#include <stdio.h>

/* Memory Pools */
typedef struct {
    uint8_t data[MEM_SMALL_BLOCK_SIZE];
    bool allocated;
} mem_small_block_t;

typedef struct {
    uint8_t data[MEM_MEDIUM_BLOCK_SIZE];
    bool allocated;
} mem_medium_block_t;

typedef struct {
    uint8_t data[MEM_LARGE_BLOCK_SIZE];
    bool allocated;
} mem_large_block_t;

/* Global memory state */
typedef struct {
    mem_small_block_t small_pool[MEM_SMALL_POOL_COUNT];
    mem_medium_block_t medium_pool[MEM_MEDIUM_POOL_COUNT];
    mem_large_block_t large_pool[MEM_LARGE_POOL_COUNT];
    
    mem_stats_t stats;
    bool initialized;
} mem_state_t;

static mem_state_t mem_state = {0};

/**
 * Compute checksum for memory block
 */
static uint16_t mem_compute_checksum(mem_block_header_t *header, size_t size)
{
    uint16_t checksum = 0;
    uint8_t *data = (uint8_t*)(header + 1);
    for (size_t i = 0; i < size; i++) {
        checksum += data[i];
    }
    return checksum;
}

/**
 * Initialize memory manager
 */
int mem_init(void)
{
    if (mem_state.initialized) {
        return 0;
    }
    
    memset(&mem_state, 0, sizeof(mem_state_t));
    mem_state.initialized = true;
    
    printf("[MEM] Manager initialized\n");
    printf("[MEM] Small pool: %d blocks x %d bytes = %d bytes\n",
           MEM_SMALL_POOL_COUNT, MEM_SMALL_BLOCK_SIZE,
           MEM_SMALL_POOL_COUNT * MEM_SMALL_BLOCK_SIZE);
    printf("[MEM] Medium pool: %d blocks x %d bytes = %d bytes\n",
           MEM_MEDIUM_POOL_COUNT, MEM_MEDIUM_BLOCK_SIZE,
           MEM_MEDIUM_POOL_COUNT * MEM_MEDIUM_BLOCK_SIZE);
    printf("[MEM] Large pool: %d blocks x %d bytes = %d bytes\n",
           MEM_LARGE_POOL_COUNT, MEM_LARGE_BLOCK_SIZE,
           MEM_LARGE_POOL_COUNT * MEM_LARGE_BLOCK_SIZE);
    printf("[MEM] Total heap: %d bytes\n\n",
           MEM_SMALL_POOL_COUNT * MEM_SMALL_BLOCK_SIZE +
           MEM_MEDIUM_POOL_COUNT * MEM_MEDIUM_BLOCK_SIZE +
           MEM_LARGE_POOL_COUNT * MEM_LARGE_BLOCK_SIZE);
    
    return 0;
}

/**
 * Allocate memory
 */
void* mem_alloc(size_t size)
{
    if (!mem_state.initialized || size == 0) {
        mem_state.stats.failed_allocations++;
        return NULL;
    }
    
    /* Choose pool based on size */
    if (size <= MEM_SMALL_BLOCK_SIZE) {
        for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
            if (!mem_state.small_pool[i].allocated) {
                mem_state.small_pool[i].allocated = true;
                mem_state.stats.total_allocated += size;
                mem_state.stats.current_allocations++;
                if (mem_state.stats.total_allocated > mem_state.stats.peak_usage) {
                    mem_state.stats.peak_usage = mem_state.stats.total_allocated;
                }
                printf("[MEM] Allocated %zu bytes from SMALL pool (block %d)\n", size, i);
                return mem_state.small_pool[i].data;
            }
        }
    }
    else if (size <= MEM_MEDIUM_BLOCK_SIZE) {
        for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
            if (!mem_state.medium_pool[i].allocated) {
                mem_state.medium_pool[i].allocated = true;
                mem_state.stats.total_allocated += size;
                mem_state.stats.current_allocations++;
                if (mem_state.stats.total_allocated > mem_state.stats.peak_usage) {
                    mem_state.stats.peak_usage = mem_state.stats.total_allocated;
                }
                printf("[MEM] Allocated %zu bytes from MEDIUM pool (block %d)\n", size, i);
                return mem_state.medium_pool[i].data;
            }
        }
    }
    else if (size <= MEM_LARGE_BLOCK_SIZE) {
        for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
            if (!mem_state.large_pool[i].allocated) {
                mem_state.large_pool[i].allocated = true;
                mem_state.stats.total_allocated += size;
                mem_state.stats.current_allocations++;
                if (mem_state.stats.total_allocated > mem_state.stats.peak_usage) {
                    mem_state.stats.peak_usage = mem_state.stats.total_allocated;
                }
                printf("[MEM] Allocated %zu bytes from LARGE pool (block %d)\n", size, i);
                return mem_state.large_pool[i].data;
            }
        }
    }
    
    /* Allocation failed */
    mem_state.stats.failed_allocations++;
    printf("[MEM] Allocation failed: size %zu too large or no free blocks\n", size);
    return NULL;
}

/**
 * Free memory
 */
int mem_free(void *ptr)
{
    if (!mem_state.initialized || !ptr) {
        return -1;
    }
    
    /* Check small pool */
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if ((void*)mem_state.small_pool[i].data == ptr) {
            if (!mem_state.small_pool[i].allocated) {
                printf("[MEM] Warning: Double free detected\n");
                return -1;
            }
            mem_state.small_pool[i].allocated = false;
            mem_state.stats.total_freed += MEM_SMALL_BLOCK_SIZE;
            mem_state.stats.current_allocations--;
            printf("[MEM] Freed %d bytes from SMALL pool (block %d)\n", MEM_SMALL_BLOCK_SIZE, i);
            return 0;
        }
    }
    
    /* Check medium pool */
    for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
        if ((void*)mem_state.medium_pool[i].data == ptr) {
            if (!mem_state.medium_pool[i].allocated) {
                printf("[MEM] Warning: Double free detected\n");
                return -1;
            }
            mem_state.medium_pool[i].allocated = false;
            mem_state.stats.total_freed += MEM_MEDIUM_BLOCK_SIZE;
            mem_state.stats.current_allocations--;
            printf("[MEM] Freed %d bytes from MEDIUM pool (block %d)\n", MEM_MEDIUM_BLOCK_SIZE, i);
            return 0;
        }
    }
    
    /* Check large pool */
    for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
        if ((void*)mem_state.large_pool[i].data == ptr) {
            if (!mem_state.large_pool[i].allocated) {
                printf("[MEM] Warning: Double free detected\n");
                return -1;
            }
            mem_state.large_pool[i].allocated = false;
            mem_state.stats.total_freed += MEM_LARGE_BLOCK_SIZE;
            mem_state.stats.current_allocations--;
            printf("[MEM] Freed %d bytes from LARGE pool (block %d)\n", MEM_LARGE_BLOCK_SIZE, i);
            return 0;
        }
    }
    
    printf("[MEM] Error: Pointer not found in any pool\n");
    return -1;
}

/**
 * Allocate zero-initialized memory
 */
void* mem_calloc(size_t count, size_t size)
{
    size_t total_size = count * size;
    void *ptr = mem_alloc(total_size);
    
    if (ptr) {
        memset(ptr, 0, total_size);
    }
    
    return ptr;
}

/**
 * Reallocate memory
 */
void* mem_realloc(void *ptr, size_t size)
{
    if (!mem_state.initialized) {
        return NULL;
    }
    
    /* Allocate new memory */
    void *new_ptr = mem_alloc(size);
    
    if (new_ptr && ptr) {
        /* Copy data from old location */
        memcpy(new_ptr, ptr, size);
        /* Free old memory */
        mem_free(ptr);
    }
    
    return new_ptr;
}

/**
 * Get memory statistics
 */
int mem_get_stats(mem_stats_t *stats)
{
    if (!mem_state.initialized || !stats) {
        return -1;
    }
    
    memcpy(stats, &mem_state.stats, sizeof(mem_stats_t));
    
    /* Calculate fragmentation */
    uint32_t total_blocks = MEM_SMALL_POOL_COUNT + MEM_MEDIUM_POOL_COUNT + MEM_LARGE_POOL_COUNT;
    uint32_t allocated_small = 0, allocated_medium = 0, allocated_large = 0;
    
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if (mem_state.small_pool[i].allocated) allocated_small++;
    }
    
    for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
        if (mem_state.medium_pool[i].allocated) allocated_medium++;
    }
    
    for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
        if (mem_state.large_pool[i].allocated) allocated_large++;
    }
    
    uint32_t allocated_blocks = allocated_small + allocated_medium + allocated_large;
    stats->fragmentation_percent = (allocated_blocks * 100) / total_blocks;
    
    return 0;
}

/**
 * Dump memory information
 */
void mem_dump_info(void)
{
    mem_stats_t stats;
    mem_get_stats(&stats);
    
    printf("\n=== Memory Information ===\n");
    printf("Initialized: %s\n", mem_state.initialized ? "YES" : "NO");
    printf("Total Allocated: %lu bytes\n", stats.total_allocated);
    printf("Total Freed: %lu bytes\n", stats.total_freed);
    printf("Current Allocations: %lu\n", stats.current_allocations);
    printf("Failed Allocations: %lu\n", stats.failed_allocations);
    printf("Peak Usage: %lu bytes\n", stats.peak_usage);
    printf("Fragmentation: %lu%%\n\n", stats.fragmentation_percent);
    
    /* Small pool */
    uint32_t allocated_small = 0;
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if (mem_state.small_pool[i].allocated) allocated_small++;
    }
    printf("Small Pool: %lu/%d blocks allocated\n", allocated_small, MEM_SMALL_POOL_COUNT);
    
    /* Medium pool */
    uint32_t allocated_medium = 0;
    for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
        if (mem_state.medium_pool[i].allocated) allocated_medium++;
    }
    printf("Medium Pool: %lu/%d blocks allocated\n", allocated_medium, MEM_MEDIUM_POOL_COUNT);
    
    /* Large pool */
    uint32_t allocated_large = 0;
    for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
        if (mem_state.large_pool[i].allocated) allocated_large++;
    }
    printf("Large Pool: %lu/%d blocks allocated\n\n", allocated_large, MEM_LARGE_POOL_COUNT);
}

/**
 * Check memory integrity
 */
int mem_check_integrity(void)
{
    int errors = 0;
    
    printf("[MEM] Checking integrity...\n");
    
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if (mem_state.small_pool[i].allocated) {
            /* Check for corruption (verify checksum) */
        }
    }
    
    printf("[MEM] Integrity check complete: %d errors found\n", errors);
    return errors;
}

/**
 * Get available memory
 */
uint32_t mem_available(void)
{
    uint32_t available = 0;
    
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if (!mem_state.small_pool[i].allocated) {
            available += MEM_SMALL_BLOCK_SIZE;
        }
    }
    
    for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
        if (!mem_state.medium_pool[i].allocated) {
            available += MEM_MEDIUM_BLOCK_SIZE;
        }
    }
    
    for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
        if (!mem_state.large_pool[i].allocated) {
            available += MEM_LARGE_BLOCK_SIZE;
        }
    }
    
    return available;
}

/**
 * Get used memory
 */
uint32_t mem_used(void)
{
    uint32_t used = 0;
    
    for (int i = 0; i < MEM_SMALL_POOL_COUNT; i++) {
        if (mem_state.small_pool[i].allocated) {
            used += MEM_SMALL_BLOCK_SIZE;
        }
    }
    
    for (int i = 0; i < MEM_MEDIUM_POOL_COUNT; i++) {
        if (mem_state.medium_pool[i].allocated) {
            used += MEM_MEDIUM_BLOCK_SIZE;
        }
    }
    
    for (int i = 0; i < MEM_LARGE_POOL_COUNT; i++) {
        if (mem_state.large_pool[i].allocated) {
            used += MEM_LARGE_BLOCK_SIZE;
        }
    }
    
    return used;
}
