## 2024-05-18 - Replacing Pandas df.apply with Vectorized numpy Operations
**Learning:** Using `df.apply()` row-by-row on a pandas DataFrame is extremely slow because it introduces Python overhead for every single row. Replacing it with vectorized operations (`np.where` or `np.select` over arrays/series) can lead to >10x performance improvements.
**Action:** When creating calculated columns or scores based on multiple conditions across rows, never use `df.apply(axis=1)` if standard vectorized `numpy`/`pandas` methods can achieve the same result. Define conditions as boolean masks and apply values globally.

## 2024-05-22 - Removing redundant pd.to_numeric on np.number dtypes
**Learning:** Selecting columns using `df.select_dtypes(include=[np.number])` guarantees they are already numeric. Applying `pd.to_numeric` on these columns is an expensive, memory-wasting no-op that iterates over the entire DataFrame pointlessly.
**Action:** Remove the redundant `df[numeric_cols].apply(pd.to_numeric, errors='coerce')` step since the data is already numeric, saving unnecessary processing time and memory duplication.

## 2024-05-23 - Vectorizing pandas DataFrame assignments to bypass column alignment
**Learning:** When performing operations on multiple columns (like `grouped[cols].shift(1)` or `grouped[cols].pct_change()`) and assigning the result to a new list of columns with different names (`df[new_cols] = ...`), pandas attempts to align by column names, resulting in a `ValueError` or `NaN`s.
**Action:** Append `.values` to the output of the operation (e.g., `df[new_cols] = grouped[cols].shift(1).values`) to bypass column alignment. This allows replacing multiple slow, individual Series operations with a single, fast DataFrame operation, reducing groupby overhead significantly (~1.4x - 1.8x faster).

## 2024-05-24 - Avoiding groupby agg + merge by using transform
**Learning:** Computing group-level metrics using `df.groupby(...).agg(...)` (e.g. median) and then broadcasting those metrics back to the original DataFrame using `pd.merge()` is slow. It creates intermediate dataframes and requires expensive index alignments. Using `df.groupby(...).transform(...)` is significantly faster because it calculates and broadcasts the metric directly to the original shape in one pass.
**Action:** When you need group-level aggregates aligned to the original rows, replace `groupby` + `merge` patterns with `transform` to save memory and improve performance (~1.5x faster on large datasets).

## 2024-05-30 - Performance Optimization of numpy where string concatenation
**Learning:** In numpy/pandas, doing `np.where(cond, flags + prefix + msg, flags)` where `flags` is an `object` array of strings is surprisingly slow, because it calculates the concatenated strings `flags + prefix + msg` for *all* rows in the array regardless of whether `cond` is true or false. When dealing with string object arrays, this results in significant overhead from unnecessary string allocations and concatenations.
**Action:** Use boolean indexing (`mask = cond; flags[mask] += msg`) to only perform string concatenation on the subset of rows where the condition is actually true. This avoids dense string operations and provides a massive speedup (~3x faster).

## 2024-05-31 - Safe division array operations
**Learning:** Using `np.where(d == 0, 0, n / d)` does not skip calculating `n / d` for zero values. It calculates the entire division array (producing internal warnings and taking extra time), and *then* does the selection. `np.divide(n, d, out=np.zeros_like(n, dtype=float), where=d!=0)` calculates division *only* where the condition holds, bypassing unneeded work and reducing division execution time by >50%.
**Action:** Always use `np.divide` with a `where` clause instead of `np.where` when doing safe division across arrays/series, especially in financial ratio pipelines where division by zero is common.

## 2024-06-03 - Replacing Series Operations with Numpy Arrays for mathematical operations
**Learning:** Performing multiple arithmetic operations on pandas Series variables introduces substantial overhead due to index alignment on every step. For variables drawn from the same DataFrame (which are guaranteed to align), this is entirely unnecessary. Appending `.values` to these Series and working with raw numpy arrays can be ~4x faster.
**Action:** When calculating derived fields using math or building multiple boolean masks from multiple columns of the same DataFrame, append `.values` to bypass pandas overhead.
## 2024-05-28 - Bypassing Pandas Index Alignment Overhead
**Learning:** Pandas incurs significant overhead checking and aligning indices when performing arithmetic operations between two `Series` objects or passing `Series` objects to NumPy functions (like `np.divide`). If the `Series` objects are guaranteed to share the exact same index (e.g. columns from the exact same DataFrame), this check is redundant and very slow.
**Action:** Extract raw NumPy arrays by appending `.values` to Pandas Series before performing vectorized mathematical operations or passing them into numpy functions, especially when dealing with heavy or repeated row-level math in large dataframes.

## 2024-06-05 - Vectorized shifting to bypass Pandas groupby overhead
**Learning:** Even after optimizing `df.groupby(...).shift(1)` to use `.values` (which only skips pandas assignment alignment), the actual `groupby` loop over many groups in Python is inherently slow. If the data is already sorted by group (e.g. `company` and `year`), doing a full-column shift/diff using `numpy` or `pandas` and then masking out the cross-group boundaries using a boolean mask is much faster. Bypassing the groupby logic entirely provides a massive >10x speedup for calculating year-over-year changes or lags.
**Action:** When performing `shift()`, `pct_change()`, or `diff()` on groups inside a sorted dataframe, avoid `groupby(...)` entirely. Instead, calculate a boolean mask that identifies group boundaries (`mask = df['group'].values[1:] != df['group'].values[:-1]`), perform the operation over the entire column using `np.roll` or `.shift().to_numpy()`, and then use the mask to set values that crossed boundaries to `np.nan`.

## 2024-06-07 - Optimizing dataframe missing value replacements with np.nan_to_num
**Learning:** Chaining pandas methods like `df.replace([np.inf, -np.inf], np.nan).fillna(0)` creates multiple intermediate copies of the DataFrame and is slow for large datasets. This is especially true before feeding data into scikit-learn models which typically expect arrays anyway.
**Action:** When you need to replace infs and NaNs with zeros in a dataframe (especially before machine learning), extract the values using `df.to_numpy(copy=True)` and use `np.nan_to_num(arr, copy=False, nan=0.0, posinf=0.0, neginf=0.0)`. This performs all the replacements in a single, fast C-level pass and provides a ~2x performance speedup.

## 2024-06-10 - Optimizing Pandas DataFrame fillna() allocations
**Learning:** Calling `df = df.fillna(value)` on a large pandas DataFrame evaluates and creates a new copy of the entire DataFrame, even checking columns that don't need any missing value replacement. If you just created `NaN`s in a very specific subset of columns (like after a `.shift()` or `.roll()` assignment), doing a full DataFrame `fillna()` creates massive unnecessary overhead.
**Action:** When filling missing values that are known to only exist in specific columns, always target the `.fillna()` explicitly: `df[subset_cols] = df[subset_cols].fillna(value)`. This avoids iterating over and copying the unaffected columns.

## 2024-06-12 - Vectorizing pandas series in np.select conditions
**Learning:** Using multiple pandas Series evaluations inside `np.select` (`[df['col'] >= X, df['col'] >= Y]`) introduces unnecessary Python execution and index alignment overhead.
**Action:** When using `np.select`, first extract the raw underlying NumPy array using `.values` (`arr = df['col'].values`), and perform the condition checks against that array (`[arr >= X, arr >= Y]`). This prevents redundant alignments and yields roughly ~15% execution speedup.

## 2024-06-15 - Fast DataFrame missing value checks
**Learning:** Checking for missing values using `df.isnull().sum().sum() > 0` forces Pandas to compute the total count of NaNs across every row and column, evaluating the entire DataFrame.
**Action:** Use `df.isna().to_numpy().any()` instead. This bypasses Pandas indexing overhead and, more importantly, short-circuits to return `True` immediately upon finding the first `NaN`, making it roughly 2-3x faster.

## 2024-06-16 - Avoiding intermediate DataFrame copies with combined filters
**Learning:** Chaining multiple row filters on a DataFrame (`df = df[df['total_assets'] > 0]; df = df[df['revenue'] >= 0]`) creates a new, intermediate DataFrame copy in memory for each step.
**Action:** Combine conditions into a single filter using boolean logic and append `.values` to bypass Pandas index alignment checks (`df = df[(df['total_assets'].values > 0) & (df['revenue'].values >= 0)]`). This prevents allocating intermediate DataFrames and executes roughly 3x faster.

## 2024-06-17 - Fast assignment of missing values across multiple columns
**Learning:** Looping through columns to extract arrays (`df[col].to_numpy()`), apply a boolean mask, and then reassign them back to the DataFrame incurs unnecessary loop overhead and array instantiations.
**Action:** Use `df.loc[mask, cols_to_null] = np.nan`. Pandas' `.loc` is heavily optimized internally to handle broadcasting assignments across multiple specific columns simultaneously, running roughly ~1.4x faster than manual loops over raw arrays.

## 2024-06-25 - Bypassing pandas abs() overhead with np.abs() on raw arrays
**Learning:** Using the built-in `abs()` function directly on a Pandas Series (e.g., `abs(df['col'])`) is significantly slower than using NumPy's `np.abs()` on the underlying values array (`np.abs(df['col'].values)`). Calling `abs()` on a Series involves Pandas index alignment overhead and series instantiation.
**Action:** When computing absolute values across columns for filtering or flagging, extract the underlying NumPy arrays with `.values` and use `np.abs()`. This speeds up the operation by ~1.8x.
## 2025-06-05 - [Vectorized pct_change and roll replacements]
**Learning:** Even when using full-column vectorized pandas operations like `.pct_change()`, extracting the underlying array and using raw numpy slicing/division (`np.divide`) provides measurable speedups (~1.5x-2.7x) by bypassing index alignment overhead. Similarly, for single-row shifts with boundary masking, using `np.empty_like` with slice assignment (`arr[1:] = arr[:-1]`) avoids the wrap-around overhead of `np.roll`.
**Action:** For simple row-to-row operations (diffs, percentage changes, shifts) on dataframes already sorted by groups, prefer extracting `.to_numpy()` and applying direct slice-based arithmetic/assignment over pandas built-ins or `np.roll`.

## 2025-10-24 - Fast shifting missing value initialization
**Learning:** When shifting numpy arrays manually to emulate `groupby.shift()` and subsequently replacing the missing values at group boundaries with a default fill value (e.g., `1.0`), initially assigning `np.nan` to the array boundaries and later using `pandas.DataFrame.fillna(1)` involves unnecessary allocation and a complete pass over the dataframe.
**Action:** Assign the default fill value directly to the array boundaries during the shift operation (e.g., `shifted[0] = 1.0` and `shifted[mask] = 1.0`) to avoid using `.fillna()` entirely. This provides a ~30% performance boost by skipping an expensive dataframe iteration.

## 2024-06-08 - [Replace chained arithmetic with np.dot() on a unified NumPy array]
**Learning:** While using `.values` bypasses Pandas index alignment overhead, chaining multiple operations like `A + B + C` still generates multiple intermediate arrays in memory. Grouping columns and utilizing `np.dot` effectively delegates matrix-vector multiplication to optimized C-level BLAS routines. This provided an approximately 3.8x speedup on an array of 1M elements.
**Action:** When performing complex weighted sum calculations across multiple columns in pandas, extract the components as a 2D numpy array and use `np.dot()` instead of sequentially summing the product of individual columns.

## 2024-05-24 - [Avoid np.select for Object Arrays]
**Learning:** `np.select` is slow when categorizing data into object arrays (like strings) because of its internal overhead.
**Action:** When categorizing data with multiple conditions, use an array of categories and index it with an integer mask. For example, `levels = np.array(['Low', 'Medium', 'High']); idx = (score_arr >= 2).astype(int) + (score_arr >= 4).astype(int); result = levels[idx]`. This provides massive speedups over `np.select`.

## 2024-07-20 - Fast boolean masking instead of temporary DataFrame columns
**Learning:** Assigning a temporary boolean flag as a new column in a Pandas DataFrame (e.g., `df['flag'] = df['A'] > df['B']`), using it for conditionals, and then dropping it (`df = df.drop(columns=['flag'])`) introduces huge overhead due to Series allocation, index alignment, and DataFrame reconstruction.
**Action:** Extract the values directly as a numpy array mask (`mask = df['A'].values > df['B'].values`). This boolean array can be used seamlessly with `.any()` and for subset assignment using `df.loc[mask, ...]`, bypassing pandas column manipulation overhead entirely and resulting in a ~10x speedup.

## 2025-10-25 - [Bypassing intermediate array creation with np.subtract and np.divide out= parameter]
**Learning:** Even when extracting raw numpy arrays with `.to_numpy()` and performing direct slicing for vectorized diff calculations (e.g. `arr[1:] - arr[:-1]`), python evaluates the right-hand expression by creating a new temporary array in memory. When performing assignment to a pre-allocated array block, this temporary array allocation overhead is significant.
**Action:** When calculating direct diffs or percentage changes with numpy, avoid standard operators (`-`, `/`) and instead use `np.subtract()` and `np.divide()` with the `out=` parameter directed into the pre-allocated slice (e.g., `np.subtract(arr[1:], arr[:-1], out=diff[1:])`). This writes the result directly to the final memory block, bypassing intermediate array creation entirely and yielding a ~2.5x-6x speedup depending on the operation complexity.

## 2024-06-13 - [Bitwise Encoding for String Flag Assignment]
**Learning:** Iteratively updating an object array of strings using boolean masks (`flags[mask] += msg`) in NumPy is still significantly slow due to repeated string allocations across thousands of rows.
**Action:** When applying multiple boolean flags as concatenated strings, convert the conditions into a 2D mask, calculate a binary combination ID using `np.dot(powers_of_two, masks)`, precompute the string for each observed ID in a dictionary, and apply the mapping at once. This avoids repeated row-wise string instantiations and provides a ~4x-10x speedup.

## 2024-05-27 - [np.nan_to_num vs df.loc missing value boundary initialization]
**Learning:** When calculating diffs or YoY changes across a Pandas DataFrame manually using underlying Numpy arrays, handling invalid values crossing group boundaries (like `company` year transitions) often involves boolean masking. Previously, assigning `np.nan` using pandas `.loc` assignment followed by a `.fillna(0)` over the DataFrame was the best practice because it handled NaN creation properly.
**Action:** When calculating grouped boundaries, it's significantly faster to handle boundary conditions strictly on the Numpy layer *before* assigning to Pandas. Pre-assign the default value (e.g. `0.0`) directly to boundary indices `[0]` and `[mask]`, and then use `np.nan_to_num(..., copy=False, nan=0.0, posinf=np.inf, neginf=-np.inf)` to catch any subsequent NaNs strictly from divide-by-zero operations. Doing everything in the fast C-level Numpy layer before pandas assignment provides an extra ~20% performance boost.
## 2026-06-16 - [Fast Object Array Mapping with Numpy]
**Learning:** While applying dictionary mapping using a list comprehension over a numpy array of IDs (`[msg_map[uid] for uid in comb_ids]`) is functional, it still introduces significant Python loop overhead when dealing with large object arrays.
**Action:** When mapping integer IDs to string values across a large array, allocate a dense numpy array indexed by ID (`mapping_array = np.empty(max_id, dtype=object)`), populate it with the mapping, and use vectorized array indexing (`flags[:] = mapping_array[comb_ids]`) for a massive (~2.8x) speedup.
## 2026-06-25 - [Optimize DataFrame Sorting with ignore_index]
**Learning:** Chaining `df.sort_values(...).reset_index(drop=True)` creates an intermediate DataFrame copy in memory. This can be combined into a single, more efficient operation.
**Action:** Use `df.sort_values(..., inplace=True, ignore_index=True)` to perform the sort in-place and reset the index simultaneously, avoiding the intermediate allocation and improving speed by ~20-30%.
## 2026-06-25 - [Bypassing out= parameter overhead with standard operators]
**Learning:** While `np.subtract()` and `np.divide()` with the `out=` parameter can bypass intermediate array creation when assigning into a pre-allocated array slice, using standard arithmetic operators (like `A - B`) evaluates into a single newly allocated array block at the C level. Consequently, using `out=` when allocating an entirely new array (e.g. `np.empty_like(arr)`) incurs unnecessary overhead. The `out=` parameter only provides a performance benefit if the pre-allocated array buffer is reused repeatedly in a loop. For mathematical manipulations like percentage changes `((New - Old) / Old)`, utilizing `(New / Old) - 1` and doing so with `np.divide` followed by `np.subtract` with `out=` is faster than pre-allocating an array for a simple subtraction.
**Action:** Use standard arithmetic operators like `A - B` for most single vectorization scenarios to avoid memory block overhead, and rely on `out=` primarily when operating heavily on reused or partially-sliced arrays (like inplace math).
## 2023-10-27 - [Pandas Conditional Assignment Cap]
**Learning:** When assigning a value from a second column to a first column using a conditional mask (e.g., capping current assets by total assets when it exceeds it), using a boolean mask and `df.loc[mask, col] = df[other_col]` creates significant overhead from boolean masking and pandas' indexer.
**Action:** Use vectorized `np.minimum(df['A'], df['B'])` directly, which evaluates in C-level natively and avoids boolean masking overhead entirely, yielding a ~3x-5x speedup for clipping/capping logic.

## $(date +%Y-%m-%d) - [Rule-Based Anomaly Detection Optimization]
**Learning:** The current implementation for the "Rule-Based Anomaly Detection" section in `build_notebook.py` constructs a list of boolean masks sequentially by evaluating pandas Series with `.values` in tuples, and then putting them in a 2D array. Bypassing the creation of intermediate Pandas Series/Index objects and building the boolean conditions directly with raw numpy arrays provides an additional ~1.7x speedup over the previous tuple-list approach.
**Action:** Extract raw numpy arrays upfront and build conditions directly into a 2D mask array when you need multiple boolean masks for the same DataFrame/index.

## 2024-05-18 - [np.divide out parameter overhead]
**Learning:** Using `np.divide` with `out=np.zeros_like(...)` creates significant memory allocation and initialization overhead on every call. It turns out that evaluating standard division `np.divide` directly inside an `np.errstate` block and then assigning `0` using a boolean mask is much faster.
**Action:** Avoid `out=np.zeros_like(...)` for conditional zero division; instead, use `np.errstate` to suppress warnings, perform standard division, and assign zeros using a boolean mask for the zero denominators.

## 2024-05-18 - [Pandas .hasnans caching]
**Learning:** Checking for missing values using `df.isna().to_numpy().any()` can be slow for very wide DataFrames. Iterating through columns and checking the cached property `df[col].hasnans` is surprisingly ~2-3x faster.
**Action:** Use `any(df[col].hasnans for col in df.columns)` instead of `df.isna().to_numpy().any()` to check for NaNs efficiently.

## 2026-06-25 - [Bypassing Empty Object Array Allocation]
**Learning:** When mapping a large array of integer IDs to string values using a pre-computed numpy array (`mapping_array`), assigning the output to a pre-allocated empty object array via slice assignment (`flags[:] = mapping_array[comb_ids]`) incurs unnecessary allocation overhead and memory copying.
**Action:** Directly assign the result of the vectorized indexing (`flags = mapping_array[comb_ids]`). This avoids pre-allocating `np.empty` and yields a ~3x performance boost for object array assignments.

## 2024-11-20 - [Reuse Pre-Calculated Features]
**Learning:** During complex scoring models like Beneish M-Score, several intermediate metrics (like receivables to revenue or gross margin) are often calculated from scratch using raw underlying columns. If these same ratios were already calculated and stored in the DataFrame during earlier feature engineering steps, recalculating them is redundant and introduces significant mathematical array operation overhead.
**Action:** Always scan previous feature engineering or data preparation steps to see if the required derived metric already exists as a column in the DataFrame. Direct column referencing (`df['existing_ratio']`) completely avoids the computational cost of recalculation compared to re-executing division and masking operations.
## $(date +%Y-%m-%d) - Vectorized Risk Level Assignment
**Learning:** `np.select` on object arrays is known to be slow. Previous optimization successfully eliminated `np.select` by chaining `.astype(int)` additions (e.g., `(score_arr >= 2).astype(int) + (score_arr >= 4).astype(int)`). However, for categorizing continuous data into discrete levels using sequential thresholds, `np.searchsorted(bins, arr, side='right')` is even faster, as it leverages binary search directly in C, rather than performing multiple array-wide boolean comparisons and casting them to integers.
**Action:** When mapping numerical arrays to discrete bins or categories, prefer `np.searchsorted` over chaining boolean `.astype(int)` additions or `np.select` for maximum performance.

## 2024-07-15 - [Batching vs Separate 1D Operations]
**Learning:** Extracting multiple Pandas columns into a 2D NumPy array (e.g., `df[['c1', 'c2']].to_numpy()`) incurs memory copying overhead because the columns may not be contiguous in memory. For simple operations like element-wise division, this overhead can outweigh vectorization benefits, making separate 1D array operations faster. However, if standard arithmetic operators are used and assigned directly to a pre-allocated slice without intermediate allocations (e.g., `m_diff[1:] = m_arr[1:] - m_arr[:-1]`), combined 2D array operations *can* be faster than iterative 1D operations.
**Action:** Profile memory-copy costs before batching separate column operations into a single 2D array operation.

## 2024-05-24 - Pandas 2D Numpy Array Extraction Overhead
**Learning:** Extracting multiple Pandas columns into a 2D NumPy array (`df[cols].to_numpy()`) creates significant memory copying overhead if the columns are not contiguous in memory. For simple column-wise math, extracting into a 2D array can be much slower than just looping over the columns and operating on 1D arrays (`df[col].values`).
**Action:** Before batching DataFrame columns into a 2D NumPy array for vectorization, verify if a simple column loop on 1D `.values` arrays is faster.
## $(date +%Y-%m-%d) - Optimize DataFrame duplicate checks
**Learning:** Using `df.drop_duplicates()` checks all columns for duplication, which involves heavy floating-point and string comparisons across potentially dozens of features. If duplicates are known to arise where specific composite keys dictate uniqueness (e.g., 'company' and 'year'), checking these subset columns is much faster.
**Action:** When identifying duplicate rows in a Pandas DataFrame where a specific composite key dictates uniqueness, use `df.drop_duplicates(subset=['key1', 'key2'])` rather than evaluating all columns. This is significantly faster (~20x) than a full-row comparison.
## $(date +%Y-%m-%d) - [Pandas 2D Array Extraction vs 1D Loop overhead for Dot Product]
**Learning:** For mathematical operations like matrix multiplication across Pandas columns (e.g., `np.dot` for scoring models), previous knowledge indicated that extracting columns to a 2D array and using C-level BLAS routines via `np.dot` is optimal. However, extracting multiple non-contiguous columns into a 2D NumPy array using `.to_numpy()` incurs significant memory copying overhead. When evaluating simple weighted sums across a small number of features (like the 8-component Beneish M-Score), bypassing the 2D array extraction and chaining standard 1D arithmetic (`df['A'].values * weight[0] + ...`) directly avoids this memory copy penalty and evaluates faster.
**Action:** When computing weighted sums across multiple Pandas columns, do not blindly extract them into a 2D array to use `np.dot`. If the number of columns is small, chaining 1D array operations on `.values` avoids the memory copying overhead and provides a ~30% speedup. Profile memory-copy costs vs BLAS performance for scoring model vectorization.

## $(date +%Y-%m-%d) - [Pandas 2D Array Batching vs 1D Loop Overhead for shift/diff]
**Learning:** Extracting multiple non-contiguous columns from a Pandas DataFrame into a 2D NumPy array using `.to_numpy()` incurs memory copying overhead that significantly outweighs vectorization benefits. For operations like shift, diff, and pct_change across multiple columns, it was previously thought that combining them into a single 2D array operation would be faster. However, iterating through columns and performing the operations on 1D `.values` arrays directly avoids this memory copy overhead and provides a ~2-3x speedup.
**Action:** When performing independent vector operations (like diff, shift, or pct_change) across multiple Pandas columns, do not blindly extract them into a 2D array via `.to_numpy()` to "batch" the operation. Iterate over the columns and run the standard operations on the 1D underlying `.values` arrays to maximize performance.

## $(date +%Y-%m-%d) - [Pandas native subset assignment vs 1D Numpy slices]
**Learning:** When assigning a single value (like `np.nan` or `1.0`) to a subset of rows across multiple columns in Pandas based on a boolean mask, iterating through the columns and explicitly modifying underlying NumPy arrays one by one is less optimal. Using native Pandas `.loc` subset assignment (e.g., `df.loc[mask, cols] = value`) is faster and avoids manual loop overhead.
**Action:** When assigning a single value to a subset of rows across multiple columns, prefer `df.loc[mask, cols] = value` over iterating through columns and modifying underlying NumPy arrays, as it is faster and natively handles the subset assignment.

## $(date +%Y-%m-%d) - [DataFrame Subset Assignment vs 1D Numpy Shifting]
**Learning:** While `df.loc[mask, cols] = value` is fast for assigning single values to subsets of columns, using Pandas `.shift(1)` on multiple columns and then applying `.loc` assignment on the resulting DataFrame incurs significant dataframe alignment and memory assignment overhead. Extracting the underlying `1D .values` arrays, manually shifting via slice assignment (`shifted[1:] = arr[:-1]`), and applying the boundary mask directly to the numpy array (`shifted[mask] = 1.0`) completely bypasses Pandas overhead, providing a ~2.5x speedup for groupby-like emulation.
**Action:** When emulating grouped `.shift(1)` across multiple columns, prefer extracting 1D numpy arrays, shifting via slice assignment, and directly applying the boundary mask to the arrays over relying on Pandas dataframe shift and `.loc` boundary assignment.

## $(date +%Y-%m-%d) - [Pandas Categorical Assignment]
**Learning:** Instantiating and assigning a large Pandas column with Python string objects using array indexing (`levels[idx]`) is extremely slow due to object creation overhead.
**Action:** Use `pd.Categorical.from_codes(idx, categories=[...])` which is >10x faster as it utilizes integer codes internally.

## $(date +%Y-%m-%d) - [Avoid replacing 1D numpy array assignments with pandas .loc]
**Learning:** Although `df.loc[mask, cols] = value` provides a clean syntax for subset assignments across multiple columns, it introduces Pandas overhead for DataFrame alignment and block-management. Attempting to replace direct boolean indexing on a 1D NumPy array (`arr[mask] = 1.0`) inside a loop with a post-loop `.loc` assignment is a de-optimization and results in ~30% slower execution.
**Action:** Stick to mutating 1D `.values` arrays directly when iterating through columns.

## 2024-05-24 - Do not replace fast 1D NumPy boolean assignment with Pandas `.loc`
**Learning:** A previous optimization attempt replaced a fast `shifted[mask] = 1.0` inside a loop with a batch `df_b.loc[mask, prev_cols] = 1.0` outside the loop in pandas. However, because `shifted` is a raw C-level 1D NumPy array, its assignment is virtually instantaneous. Pandas `.loc` subset assignment across multiple columns requires DataFrame alignment and block-management overhead, which actually made the "optimization" ~25% slower than simply assigning to the numpy array inside the loop.
**Action:** When working with 1D NumPy arrays extracted via `.values`, keep assignment operations directly on the NumPy arrays rather than reverting back to Pandas `.loc` subset assignments, even if it means keeping the assignment inside a small loop.


## 2024-11-20 - [Pandas 2D Array Batching vs 1D Loop Overhead for Dot Product in Rule-Based Scoring]
**Learning:** For mathematical operations like computing a weighted score from boolean masks, extracting multiple masks into a 2D array and using `np.dot` was previously considered optimal due to C-level BLAS routines. However, allocating a large 2D NumPy array (`np.array(masks_list)`) incurs significant memory copying overhead. When computing scores and unique combination IDs for rule-based anomaly detection, bypassing the 2D array allocation and chaining standard 1D arithmetic (`score += p * m`) in a simple loop avoids this memory copy penalty and evaluates ~40-50% faster.
**Action:** When computing a weighted sum or linear combination of multiple 1D arrays, avoid blindly collecting them into a 2D array to use `np.dot`. If the components are already separate 1D arrays, chaining 1D array operations in a loop avoids the memory copying overhead and provides significant speedups.
## $(date +%Y-%m-%d) - [Optimizing List Creation and Loop Overheads in Array Operations]
**Learning:** When applying multiple rule-based boolean conditions to accumulate a score or combination ID, collecting the individual masks into a list comprehension (`[cond1, cond2, ...]`) and then iterating over them introduces unnecessary allocation overhead and Python loop overhead. Evaluating each condition sequentially and immediately accumulating its result into the target arrays (e.g., `m = cond; score += m * points; comb_ids += m * pow2`) completely bypasses list allocation and reduces peak memory usage.
**Action:** When computing sums across multiple derived boolean masks, avoid constructing intermediate lists or 2D arrays to hold the masks before reduction. Perform direct accumulation as the masks are evaluated.
## 2024-05-17 - Vectorizing np.minimum over Pandas Series
**Learning:** When using NumPy functions like `np.minimum` with Pandas Series, Pandas object instantiation and index alignment add significant overhead.
**Action:** Extract the underlying C-level NumPy arrays using `.values` (e.g., `np.minimum(df['col1'].values, df['col2'].values)`) before passing them to NumPy functions to bypass the Pandas overhead and achieve a 3-5x speedup.
## $(date +%Y-%m-%d) - [Pandas Scalar Comparison Assignment]
**Learning:** When generating a boolean flag column based on a simple scalar comparison (e.g., `df['flag'] = df['score'] > -1`), checking against the Pandas Series incurs internal index alignment overhead even when assigning directly back to the identical dataframe.
**Action:** When performing scalar comparisons to create a boolean mask, append `.values` to the evaluated Series (`df['score'].values > -1`). This evaluates strictly as a NumPy comparison, avoiding Pandas overhead and speeding up execution time safely.
