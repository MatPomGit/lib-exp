package pl.edu.prz.arcadhd.audio

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class EngineeringAudioCounterbalanceTest {
    private val plans = (0 until EngineeringAudioCounterbalance.SEQUENCE_COUNT)
        .map(EngineeringAudioCounterbalance::sequence)

    @Test fun coversEveryOrderWithBothAlternatingStartingSides() {
        assertEquals(12, plans.size)
        assertEquals(12, plans.map { it.conditions to it.alternatingFirstChannel }.toSet().size)
        assertEquals(6, plans.count { it.alternatingFirstChannel == FirstChannel.LEFT })
        assertEquals(6, plans.count { it.alternatingFirstChannel == FirstChannel.RIGHT })
        plans.forEach { assertEquals(StereoCondition.values().toSet(), it.conditions.toSet()) }
    }

    @Test fun balancesPositionOfEveryConditionAndStartingSide() {
        for (position in 0..2) {
            for (condition in StereoCondition.values()) {
                assertEquals(4, plans.count { it.conditions[position] == condition })
                for (side in FirstChannel.values()) {
                    assertEquals(2, plans.count {
                        it.conditions[position] == condition && it.alternatingFirstChannel == side
                    })
                }
            }
        }
    }

    @Test fun deterministicIndicesAndNoHiddenRandomAllocation() {
        plans.forEach { sequence ->
            assertEquals(sequence, EngineeringAudioCounterbalance.sequence(sequence.sequenceId))
        }
    }

    @Test fun invalidSequenceIdsFailClosed() {
        for (id in listOf(-1, 12, Int.MAX_VALUE)) {
            var rejected = false
            try {
                EngineeringAudioCounterbalance.sequence(id)
            } catch (_: IllegalArgumentException) {
                rejected = true
            }
            assertTrue(rejected)
        }
    }
}
