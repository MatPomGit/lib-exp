package pl.edu.prz.arcadhd.audio

/** Technical bench sequence only. Not randomized participant assignment. */
data class EngineeringAudioSequence(
    val sequenceId: Int,
    val conditions: List<StereoCondition>,
    val alternatingFirstChannel: FirstChannel,
)

/**
 * Full 3! order permutations crossed with the two initial alternating sides.
 * No seed, participant identifier, allocation concealment or study API is present.
 */
object EngineeringAudioCounterbalance {
    const val SEQUENCE_COUNT = 12

    private val orders = listOf(
        listOf(StereoCondition.ALTERNATING, StereoCondition.MATCHED_STEREO, StereoCondition.QUIET),
        listOf(StereoCondition.ALTERNATING, StereoCondition.QUIET, StereoCondition.MATCHED_STEREO),
        listOf(StereoCondition.MATCHED_STEREO, StereoCondition.ALTERNATING, StereoCondition.QUIET),
        listOf(StereoCondition.MATCHED_STEREO, StereoCondition.QUIET, StereoCondition.ALTERNATING),
        listOf(StereoCondition.QUIET, StereoCondition.ALTERNATING, StereoCondition.MATCHED_STEREO),
        listOf(StereoCondition.QUIET, StereoCondition.MATCHED_STEREO, StereoCondition.ALTERNATING),
    )

    fun sequence(sequenceId: Int): EngineeringAudioSequence {
        require(sequenceId in 0 until SEQUENCE_COUNT) { "invalid_bench_sequence" }
        return EngineeringAudioSequence(
            sequenceId = sequenceId,
            conditions = orders[sequenceId % orders.size],
            alternatingFirstChannel = if (sequenceId < orders.size) {
                FirstChannel.LEFT
            } else {
                FirstChannel.RIGHT
            },
        )
    }
}
