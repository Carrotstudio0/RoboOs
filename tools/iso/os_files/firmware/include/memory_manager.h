/**
 * Memory Manager Header File
 * مدير الذاكرة
 */

#ifndef MEMORY_MANAGER_H
#define MEMORY_MANAGER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Memory Pool Sizes */
#define MEM_SMALL_BLOCK_SIZE    32     /* Small allocations (32 bytes) */
#define MEM_SMALL_POOL_COUNT    64     /* 2 KB total */
#define MEM_MEDIUM_BLOCK_SIZE   128    /* Medium allocations (128 bytes) */
#define MEM_MEDIUM_POOL_COUNT   32     /* 4 KB total */
#define MEM_LARGE_BLOCK_SIZE    512    /* Large allocations (512 bytes) */
#define MEM_LARGE_POOL_COUNT    16     /* 8 KB total */

/* Total heap: ~14 KB */

/* Memory Block Types */
typedef enum {
    MEM_POOL_SMALL = 0,
    MEM_POOL_MEDIUM = 1,
    MEM_POOL_LARGE = 2,
    MEM_POOL_INVALID = 3
} mem_pool_type_t;

/* Memory Block Header */
typedef struct {
    uint16_t size;
    mem_pool_type_t pool_type;
    bool allocated;
    uint16_t checksum;
} mem_block_header_t;

/* Memory Statistics */
typedef struct {
    uint32_t total_allocated;
    uint32_t total_freed;
    uint32_t current_allocations;
    uint32_t failed_allocations;
    uint32_t fragmentation_percent;
    uint32_t peak_usage;
} mem_stats_t;

/* Function Prototypes */

/**
 * Initialize memory manager
 * تهيئة مدير الذاكرة
 * @return 0 on success, -1 on error
 */
int mem_init(void);

/**
 * Allocate memory
 * تخصيص ذاكرة
 * @param size Size to allocate in bytes
 * @return Pointer to allocated memory, NULL on failure
 */
void* mem_alloc(size_t size);

/**
 * Free memory
 * تحرير ذاكرة
 * @param ptr Pointer to memory to free
 * @return 0 on success, -1 on error
 */
int mem_free(void *ptr);

/**
 * Allocate zero-initialized memory
 * تخصيص ذاكرة صفرية
 * @param count Number of elements
 * @param size Size of each element
 * @return Pointer to allocated memory, NULL on failure
 */
void* mem_calloc(size_t count, size_t size);

/**
 * Reallocate memory
 * إعادة تخصيص ذاكرة
 * @param ptr Pointer to existing memory
 * @param size New size
 * @return Pointer to reallocated memory, NULL on failure
 */
void* mem_realloc(void *ptr, size_t size);

/**
 * Get memory statistics
 * الحصول على إحصائيات الذاكرة
 * @param stats Pointer to stats structure
 * @return 0 on success, -1 on error
 */
int mem_get_stats(mem_stats_t *stats);

/**
 * Dump memory information
 * عرض معلومات الذاكرة
 */
void mem_dump_info(void);

/**
 * Check memory integrity
 * التحقق من تكامل الذاكرة
 * @return Number of errors found
 */
int mem_check_integrity(void);

/**
 * Get available memory
 * الحصول على الذاكرة المتاحة
 * @return Available memory in bytes
 */
uint32_t mem_available(void);

/**
 * Get used memory
 * الحصول على الذاكرة المستخدمة
 * @return Used memory in bytes
 */
uint32_t mem_used(void);

#endif /* MEMORY_MANAGER_H */
